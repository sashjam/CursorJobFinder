<?php

namespace App\Services;

use App\Models\Subscription;
use App\Models\User;
use App\Models\Vacancy;
use App\Support\JobDeskPython;
use Carbon\Carbon;
use Illuminate\Support\Facades\Process;
use RuntimeException;

class JobDeskFetchService
{
    public function __construct(
        private readonly UserSettingsService $settings,
    ) {}

    /** @return array<string, mixed> */
    public function fetchForUser(User $user): array
    {
        $subs = Subscription::query()
            ->where('user_id', $user->id)
            ->orderBy('id')
            ->get();

        $config = [
            'subscriptions' => $subs->map(fn (Subscription $s) => [
                'id' => $s->id,
                'name' => $s->name,
                'source' => $s->source,
                'query' => $s->query,
                'exclude_words' => $s->exclude_words,
                'enabled' => $s->enabled,
            ])->values()->all(),
            'settings' => $this->settings->fetchSettings($user),
        ];

        $projectRoot = dirname(base_path());
        $python = JobDeskPython::executable();
        $script = $projectRoot.DIRECTORY_SEPARATOR.'tools'.DIRECTORY_SEPARATOR.'fetch_worker.py';

        $result = Process::path($projectRoot)
            ->timeout(300)
            ->env(JobDeskPython::processEnvironment($projectRoot))
            ->input(json_encode($config, JSON_UNESCAPED_UNICODE))
            ->run([$python, $script]);

        $stdout = trim($result->output());
        $stderr = trim($result->errorOutput());

        /** @var array<string, mixed>|null $payload */
        $payload = $stdout !== '' ? json_decode($stdout, true) : null;

        if (! is_array($payload)) {
            $hint = $stderr !== '' ? $stderr : ($stdout !== '' ? $stdout : 'Пустой ответ Python');
            throw new RuntimeException(
                "Не удалось запустить парсер ({$python}). {$hint}"
            );
        }

        if (($payload['ok'] ?? true) === false) {
            $errors = $payload['errors'] ?? [];
            throw new RuntimeException(
                is_array($errors) && $errors !== []
                    ? implode(' ', array_map('strval', $errors))
                    : 'Опрос завершился с ошибкой'
            );
        }

        if (! $result->successful() && $stderr !== '') {
            throw new RuntimeException($stderr);
        }

        $now = now();
        foreach ($payload['vacancies'] ?? [] as $row) {
            $dedupe = (string) ($row['dedupe_key'] ?? ($row['source'].':'.($row['external_id'] ?? $row['id'])));
            $vacancy = Vacancy::query()->firstOrNew([
                'user_id' => $user->id,
                'dedupe_key' => $dedupe,
            ]);
            $isNew = ! $vacancy->exists;
            $vacancy->fill([
                'external_id' => (string) ($row['external_id'] ?? ''),
                'source' => (string) ($row['source'] ?? ''),
                'subscription_id' => $row['subscription_id'] ?? null,
                'title' => (string) ($row['title'] ?? ''),
                'company' => (string) ($row['company'] ?? ''),
                'url' => (string) ($row['url'] ?? ''),
                'description' => (string) ($row['description'] ?? ''),
                'city' => (string) ($row['city'] ?? ''),
                'published_at' => ! empty($row['published_at'])
                    ? Carbon::parse($row['published_at'])
                    : null,
                'first_seen_at' => $vacancy->first_seen_at
                    ?? (! empty($row['first_seen_at']) ? Carbon::parse($row['first_seen_at']) : $now),
                'is_new' => $isNew ? true : $vacancy->is_new,
            ]);
            $vacancy->save();
        }

        Subscription::query()
            ->where('user_id', $user->id)
            ->where('enabled', true)
            ->update(['last_checked_at' => $now]);

        return $payload;
    }
}
