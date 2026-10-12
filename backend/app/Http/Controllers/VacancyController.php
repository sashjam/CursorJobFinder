<?php

namespace App\Http\Controllers;

use App\Models\Vacancy;
use Illuminate\Http\Request;

class VacancyController extends Controller
{
    public function index(Request $request)
    {
        $newOnly = $request->boolean('new_only');
        $limit = min(500, max(1, (int) $request->query('limit', 500)));

        $query = Vacancy::query()
            ->where('user_id', $request->user()->id)
            ->orderByRaw('COALESCE(published_at, first_seen_at) DESC')
            ->limit($limit);

        if ($newOnly) {
            $query->where('is_new', true);
        }

        $items = $query->get();
        $newCount = Vacancy::query()
            ->where('user_id', $request->user()->id)
            ->where('is_new', true)
            ->count();

        return response()->json([
            'items' => $items,
            'new_count' => $newCount,
        ]);
    }

    public function markSeen(Request $request, Vacancy $vacancy)
    {
        $this->authorizeVacancy($request, $vacancy);
        $vacancy->update(['is_new' => false]);

        return response()->json(['ok' => true]);
    }

    public function markAllSeen(Request $request)
    {
        Vacancy::query()
            ->where('user_id', $request->user()->id)
            ->where('is_new', true)
            ->update(['is_new' => false]);

        return response()->json(['ok' => true]);
    }

    private function authorizeVacancy(Request $request, Vacancy $vacancy): void
    {
        if ($vacancy->user_id !== $request->user()->id) {
            abort(404);
        }
    }
}
