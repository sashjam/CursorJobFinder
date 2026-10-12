<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('subscriptions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('source', 64);
            $table->string('query')->default('');
            $table->text('exclude_words')->default('');
            $table->boolean('enabled')->default(true);
            $table->timestamp('last_checked_at')->nullable();
            $table->timestamps();
        });

        Schema::create('vacancies', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('dedupe_key');
            $table->string('external_id');
            $table->string('source', 64);
            $table->foreignId('subscription_id')->nullable()->constrained()->nullOnDelete();
            $table->string('title');
            $table->string('company')->default('');
            $table->text('url');
            $table->text('description')->default('');
            $table->string('city')->default('');
            $table->timestamp('published_at')->nullable();
            $table->timestamp('first_seen_at');
            $table->boolean('is_new')->default(true);
            $table->timestamps();

            $table->unique(['user_id', 'dedupe_key']);
            $table->index(['user_id', 'is_new']);
        });

        Schema::create('user_settings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('key');
            $table->text('value');
            $table->timestamps();

            $table->unique(['user_id', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('user_settings');
        Schema::dropIfExists('vacancies');
        Schema::dropIfExists('subscriptions');
    }
};
