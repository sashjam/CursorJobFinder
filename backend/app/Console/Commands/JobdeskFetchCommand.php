<?php

namespace App\Console\Commands;

use App\Models\User;
use App\Services\JobDeskFetchService;
use Illuminate\Console\Command;

class JobdeskFetchCommand extends Command
{
    protected $signature = 'jobdesk:fetch
                            {--user= : ID пользователя (если не указан — все с включёнными подписками)}';

    protected $description = 'Опрос сайтов через Python (для cron, если proc_open из UI недоступен)';

    public function handle(JobDeskFetchService $fetch): int
    {
        $userId = $this->option('user');
        $query = User::query()->orderBy('id');

        if ($userId !== null && $userId !== '') {
            $query->where('id', (int) $userId);
        }

        $users = $query->get();
        if ($users->isEmpty()) {
            $this->warn('Пользователи не найдены.');

            return self::SUCCESS;
        }

        $errors = 0;
        foreach ($users as $user) {
            $this->line("User #{$user->id} ({$user->email})…");
            try {
                $result = $fetch->fetchForUser($user);
                $this->info(
                    '  ok: new='.($result['new_count'] ?? 0)
                    .', kept='.($result['kept_total'] ?? 0)
                );
                foreach ($result['errors'] ?? [] as $msg) {
                    if (is_string($msg) && $msg !== '') {
                        $this->warn('  '.$msg);
                    }
                }
            } catch (\Throwable $e) {
                $errors++;
                $this->error('  '.$e->getMessage());
            }
        }

        return $errors > 0 ? self::FAILURE : self::SUCCESS;
    }
}
