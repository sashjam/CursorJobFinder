<?php

namespace App\Services;

use App\Models\User;
use App\Models\UserSetting;

class UserSettingsService
{
    private const DEFAULTS = [
        'poll_interval_minutes' => '15',
        'desired_vacancy' => '',
        'desired_vacancy_updated_at' => '',
        'use_desired_vacancy_search' => '1',
        'use_desired_post_filter' => '0',
        'desired_locations' => '[]',
    ];

    public function get(User $user, string $key, ?string $default = null): string
    {
        $row = UserSetting::query()
            ->where('user_id', $user->id)
            ->where('key', $key)
            ->first();

        if ($row !== null) {
            return $row->value;
        }

        return $default ?? (self::DEFAULTS[$key] ?? '');
    }

    public function set(User $user, string $key, string $value): void
    {
        UserSetting::query()->updateOrCreate(
            ['user_id' => $user->id, 'key' => $key],
            ['value' => $value],
        );
    }

    /** @return array<string, mixed> */
    public function desiredPayload(User $user): array
    {
        return [
            'desired_vacancy' => $this->get($user, 'desired_vacancy'),
            'desired_vacancy_updated_at' => $this->get($user, 'desired_vacancy_updated_at'),
            'use_desired_vacancy_search' => $this->get($user, 'use_desired_vacancy_search') !== '0',
            'use_desired_post_filter' => $this->get($user, 'use_desired_post_filter') === '1',
            'desired_locations' => json_decode($this->get($user, 'desired_locations', '[]'), true) ?: [],
            'poll_interval_minutes' => (int) $this->get($user, 'poll_interval_minutes', '15'),
        ];
    }

    /** @return array<string, mixed> */
    public function fetchSettings(User $user): array
    {
        return [
            'desired_vacancy' => $this->get($user, 'desired_vacancy'),
            'use_desired_vacancy_search' => $this->get($user, 'use_desired_vacancy_search') !== '0',
            'use_desired_post_filter' => $this->get($user, 'use_desired_post_filter') === '1',
            'desired_locations' => $this->get($user, 'desired_locations', '[]'),
        ];
    }
}
