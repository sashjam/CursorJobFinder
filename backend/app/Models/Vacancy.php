<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Vacancy extends Model
{
    protected $fillable = [
        'user_id',
        'dedupe_key',
        'external_id',
        'source',
        'subscription_id',
        'title',
        'company',
        'url',
        'description',
        'city',
        'published_at',
        'first_seen_at',
        'is_new',
    ];

    protected function casts(): array
    {
        return [
            'published_at' => 'datetime',
            'first_seen_at' => 'datetime',
            'is_new' => 'boolean',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function subscription(): BelongsTo
    {
        return $this->belongsTo(Subscription::class);
    }
}
