// ESLint 9.x configuration (CommonJS format)
module.exports = [
    {
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "script",
            globals: {
                // Browser globals
                window: "readonly",
                document: "readonly",
                console: "readonly",
                navigator: "readonly",
                localStorage: "readonly",
                sessionStorage: "readonly",
                location: "readonly",
                history: "readonly",
                
                // Browser APIs
                fetch: "readonly",
                setTimeout: "readonly",
                clearTimeout: "readonly",
                setInterval: "readonly",
                clearInterval: "readonly",
                requestAnimationFrame: "readonly",
                alert: "readonly",
                confirm: "readonly",
                prompt: "readonly",
                
                // DOM APIs
                FormData: "readonly",
                FileReader: "readonly",
                DOMParser: "readonly",
                URL: "readonly",
                EventTarget: "readonly",
                
                // External libraries
                MathJax: "writable",
                bootstrap: "readonly",
                CodeMirror: "readonly",
                hljs: "readonly",
                Quill: "readonly",
                Cropper: "readonly"
            }
        },
        rules: {
            "no-unused-vars": "warn",
            "no-console": "off",
            "no-undef": "error",
            "no-unused-expressions": "warn",
            "prefer-const": "warn"
        }
    },
    {
        ignores: [
            "static/**/*.css",
            "*.py",
            "*.sql",
            "*.md",
            "venv/**",
            "node_modules/**",
            "__pycache__/**"
        ]
    }
];
