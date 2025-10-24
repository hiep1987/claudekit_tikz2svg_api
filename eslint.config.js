// ESLint 9.x configuration (CommonJS format)
module.exports = [
    {
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "script",
            globals: {
                window: "readonly",
                document: "readonly",
                console: "readonly",
                MathJax: "writable"
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
