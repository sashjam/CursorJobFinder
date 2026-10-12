<?php

namespace App\Http\Controllers;

use App\Models\Subscription;
use Illuminate\Http\Request;

class SubscriptionController extends Controller
{
    public function index(Request $request)
    {
        $items = Subscription::query()
            ->where('user_id', $request->user()->id)
            ->orderBy('id')
            ->get();

        return response()->json(['items' => $items]);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'source' => ['required', 'string', 'max:64'],
            'query' => ['nullable', 'string', 'max:500'],
            'exclude_words' => ['nullable', 'string', 'max:2000'],
        ]);

        $sub = Subscription::query()->create([
            'user_id' => $request->user()->id,
            'name' => $data['name'],
            'source' => $data['source'],
            'query' => $data['query'] ?? '',
            'exclude_words' => $data['exclude_words'] ?? '',
            'enabled' => true,
        ]);

        return response()->json(['item' => $sub], 201);
    }

    public function updateEnabled(Request $request, Subscription $subscription)
    {
        $this->authorizeSub($request, $subscription);
        $data = $request->validate(['enabled' => ['required', 'boolean']]);
        $subscription->update(['enabled' => $data['enabled']]);

        return response()->json(['item' => $subscription->fresh()]);
    }

    public function destroy(Request $request, Subscription $subscription)
    {
        $this->authorizeSub($request, $subscription);
        $subscription->delete();

        return response()->json(['ok' => true]);
    }

    private function authorizeSub(Request $request, Subscription $subscription): void
    {
        if ($subscription->user_id !== $request->user()->id) {
            abort(404);
        }
    }
}
