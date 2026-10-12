<?php

namespace App\Http\Controllers;

use App\Services\JobDeskFetchService;
use Illuminate\Http\Request;

class FetchController extends Controller
{
    public function __construct(private readonly JobDeskFetchService $fetch) {}

    public function run(Request $request)
    {
        try {
            $result = $this->fetch->fetchForUser($request->user());
        } catch (\Throwable $e) {
            return response()->json([
                'ok' => false,
                'message' => $e->getMessage(),
            ], 500);
        }

        return response()->json([
            'ok' => true,
            'errors' => $result['errors'] ?? [],
            'checked_subscriptions' => $result['checked_subscriptions'] ?? 0,
            'raw_total' => $result['raw_total'] ?? 0,
            'kept_total' => $result['kept_total'] ?? 0,
            'new_count' => $result['new_count'] ?? 0,
        ]);
    }
}
