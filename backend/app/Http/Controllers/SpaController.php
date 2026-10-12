<?php

namespace App\Http\Controllers;

use Symfony\Component\HttpFoundation\BinaryFileResponse;

class SpaController extends Controller
{
    public function index(): BinaryFileResponse
    {
        $path = public_path('spa-index.html');
        if (! is_file($path)) {
            abort(
                503,
                'SPA не собран. Выполните: python tools/deploy_web.py (или npm run build в frontend и скопируйте dist).'
            );
        }

        return response()->file($path, [
            'Content-Type' => 'text/html; charset=UTF-8',
            'Cache-Control' => 'no-cache',
        ]);
    }
}
