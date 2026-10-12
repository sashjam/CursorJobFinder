<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\DesiredController;
use App\Http\Controllers\FetchController;
use App\Http\Controllers\MetaController;
use App\Http\Controllers\SubscriptionController;
use App\Http\Controllers\VacancyController;
use Illuminate\Support\Facades\Route;

Route::post('/register', [AuthController::class, 'register']);
Route::post('/login', [AuthController::class, 'login']);

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/user', [AuthController::class, 'user']);

    Route::get('/meta/sources', [MetaController::class, 'sources']);

    Route::get('/vacancies', [VacancyController::class, 'index']);
    Route::post('/vacancies/mark-all-seen', [VacancyController::class, 'markAllSeen']);
    Route::post('/vacancies/{vacancy}/seen', [VacancyController::class, 'markSeen']);

    Route::get('/subscriptions', [SubscriptionController::class, 'index']);
    Route::post('/subscriptions', [SubscriptionController::class, 'store']);
    Route::patch('/subscriptions/{subscription}', [SubscriptionController::class, 'updateEnabled']);
    Route::delete('/subscriptions/{subscription}', [SubscriptionController::class, 'destroy']);

    Route::get('/desired', [DesiredController::class, 'show']);
    Route::put('/desired', [DesiredController::class, 'update']);

    Route::post('/fetch', [FetchController::class, 'run']);
});
