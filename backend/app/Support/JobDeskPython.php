<?php

namespace App\Support;

use Illuminate\Support\Facades\Process;

final class JobDeskPython
{
    public static function executable(): string
    {
        static $cached = null;
        if ($cached !== null) {
            return $cached;
        }

        $configured = trim((string) env('JOBDESK_PYTHON', ''));
        if ($configured !== '' && $configured !== 'python' && $configured !== 'python3') {
            return $cached = $configured;
        }

        if (PHP_OS_FAMILY === 'Windows') {
            $probe = Process::run(['where.exe', 'python']);
            if ($probe->successful()) {
                foreach (preg_split('/\r?\n/', trim($probe->output())) as $line) {
                    $line = trim($line);
                    if ($line === '') {
                        continue;
                    }
                    if (stripos($line, 'WindowsApps') !== false) {
                        continue;
                    }
                    if (is_file($line)) {
                        return $cached = $line;
                    }
                }
            }
        } else {
            foreach (['python3', 'python'] as $candidate) {
                $probe = Process::run(['which', $candidate]);
                if ($probe->successful()) {
                    $path = trim($probe->output());
                    if ($path !== '' && is_file($path)) {
                        return $cached = $path;
                    }
                }
            }
        }

        return $cached = 'python';
    }

    /** @return array<string, string> */
    public static function processEnvironment(string $projectRoot): array
    {
        static $userSite = null;
        $python = self::executable();

        if ($userSite === null) {
            $probe = Process::run([$python, '-c', 'import site; print(site.getusersitepackages())']);
            $userSite = $probe->successful() ? trim($probe->output()) : '';
        }

        $pythonPath = $projectRoot;
        if ($userSite !== '' && is_dir($userSite)) {
            $pythonPath .= PATH_SEPARATOR.$userSite;
        }

        $extraPath = trim((string) env('JOBDESK_PYTHONPATH', ''));
        if ($extraPath !== '') {
            $pythonPath .= PATH_SEPARATOR.$extraPath;
        }

        $env = [
            'PYTHONPATH' => $pythonPath,
            'PYTHONIOENCODING' => 'utf-8',
        ];

        foreach (['USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'HOME', 'SystemRoot'] as $key) {
            $value = getenv($key);
            if ($value !== false && $value !== '') {
                $env[$key] = $value;
            }
        }

        return $env;
    }
}
