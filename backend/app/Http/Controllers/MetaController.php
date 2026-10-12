<?php

namespace App\Http\Controllers;

class MetaController extends Controller
{
    public function sources()
    {
        return response()->json([
            'sources' => config('jobdesk.sources'),
            'city_options' => config('jobdesk.city_options'),
        ]);
    }
}
