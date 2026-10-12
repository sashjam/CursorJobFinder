<?php

namespace App\Http\Controllers;

use App\Services\UserSettingsService;
use Illuminate\Http\Request;

class DesiredController extends Controller
{
    public function __construct(private readonly UserSettingsService $settings) {}

    public function show(Request $request)
    {
        return response()->json($this->settings->desiredPayload($request->user()));
    }

    public function update(Request $request)
    {
        $data = $request->validate([
            'desired_vacancy' => ['nullable', 'string', 'max:20000'],
            'use_desired_vacancy_search' => ['boolean'],
            'use_desired_post_filter' => ['boolean'],
            'desired_locations' => ['array'],
            'desired_locations.*' => ['string', 'max:128'],
            'poll_interval_minutes' => ['nullable', 'integer', 'min:1', 'max:1440'],
        ]);

        $user = $request->user();

        if (array_key_exists('desired_vacancy', $data)) {
            $this->settings->set($user, 'desired_vacancy', $data['desired_vacancy'] ?? '');
            $this->settings->set($user, 'desired_vacancy_updated_at', now()->toIso8601String());
        }
        if (array_key_exists('use_desired_vacancy_search', $data)) {
            $this->settings->set(
                $user,
                'use_desired_vacancy_search',
                $data['use_desired_vacancy_search'] ? '1' : '0',
            );
        }
        if (array_key_exists('use_desired_post_filter', $data)) {
            $this->settings->set(
                $user,
                'use_desired_post_filter',
                $data['use_desired_post_filter'] ? '1' : '0',
            );
        }
        if (array_key_exists('desired_locations', $data)) {
            $this->settings->set(
                $user,
                'desired_locations',
                json_encode($data['desired_locations'], JSON_UNESCAPED_UNICODE),
            );
        }
        if (array_key_exists('poll_interval_minutes', $data)) {
            $this->settings->set(
                $user,
                'poll_interval_minutes',
                (string) max(1, min(1440, (int) $data['poll_interval_minutes'])),
            );
        }

        return response()->json($this->settings->desiredPayload($user));
    }
}
