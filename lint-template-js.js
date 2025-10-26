#!/usr/bin/env node

// Comprehensive HTML Template JavaScript Linter
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TemplateJSLinter {
    constructor() {
        this.tempFiles = [];
        this.errors = [];
        this.warnings = [];
    }

    extractJavaScriptFromHtml(filePath) {
        const content = fs.readFileSync(filePath, 'utf8');
        const jsBlocks = [];
        
        // Extract JavaScript from <script> tags (excluding external scripts)
        const scriptRegex = /<script[^>]*(?!.*src=).*?>([\s\S]*?)<\/script>/gi;
        let match;
        
        while ((match = scriptRegex.exec(content)) !== null) {
            const jsCode = match[1].trim();
            if (jsCode) {
                // Find line number where this script starts
                const beforeScript = content.substring(0, match.index);
                const lineNum = (beforeScript.match(/\n/g) || []).length + 1;
                
                jsBlocks.push({
                    code: jsCode,
                    startLine: lineNum,
                    endLine: lineNum + (jsCode.match(/\n/g) || []).length,
                    original: jsCode
                });
            }
        }
        
        return jsBlocks;
    }

    cleanJinjaTemplate(jsCode) {
        // Remove or replace Jinja2 template syntax to make it valid JavaScript
        let cleaned = jsCode;
        
        // Handle complex Jinja2 expressions (if/else statements)
        cleaned = cleaned.replace(/{%\s*if.*?%}.*?{%\s*else.*?%}.*?{%\s*endif.*?%}/gs, 'null');
        
        // Remove remaining {% %} blocks
        cleaned = cleaned.replace(/{%.*?%}/g, '');
        
        // Replace {{ }} variables with null
        cleaned = cleaned.replace(/{{.*?}}/g, 'null');
        
        // Clean up multiple nulls that might have been created
        cleaned = cleaned.replace(/null\s*null/g, 'null');
        
        // Clean up extra whitespace
        cleaned = cleaned.replace(/\n\s*\n/g, '\n');
        
        return cleaned.trim();
    }

    async lintJavaScript(jsBlocks, templatePath) {
        console.log(`🔍 Analyzing JavaScript in: ${templatePath}`);
        console.log(`📊 Found ${jsBlocks.length} JavaScript block(s)\n`);

        for (let i = 0; i < jsBlocks.length; i++) {
            const block = jsBlocks[i];
            const tempFile = `temp_lint_${i + 1}_${Date.now()}.js`;
            const cleanedCode = this.cleanJinjaTemplate(block.code);

            console.log(`📝 Block ${i + 1} (lines ${block.startLine}-${block.endLine}):`);
            console.log('─'.repeat(60));
            console.log(cleanedCode);
            console.log('─'.repeat(60));

            // Write cleaned code to temp file
            fs.writeFileSync(tempFile, cleanedCode);
            this.tempFiles.push(tempFile);

            try {
                // Run ESLint on the temp file
                const result = execSync(`npx eslint ${tempFile}`, { 
                    encoding: 'utf8',
                    stdio: 'pipe'
                });
                console.log(`✅ Block ${i + 1}: No issues found`);
            } catch (error) {
                if (error.stdout) {
                    console.log(`⚠️  Block ${i + 1}: ESLint issues found:`);
                    console.log(error.stdout);
                    this.errors.push({
                        block: i + 1,
                        lines: `${block.startLine}-${block.endLine}`,
                        output: error.stdout
                    });
                }
            }
            console.log();
        }
    }

    async lintTemplate(templatePath) {
        try {
            const jsBlocks = this.extractJavaScriptFromHtml(templatePath);
            await this.lintJavaScript(jsBlocks, templatePath);
        } catch (error) {
            console.error(`❌ Error processing ${templatePath}:`, error.message);
        }
    }

    cleanup() {
        // Remove temporary files
        this.tempFiles.forEach(file => {
            if (fs.existsSync(file)) {
                fs.unlinkSync(file);
            }
        });
    }

    printSummary() {
        console.log('\n' + '='.repeat(80));
        console.log('📋 JAVASCRIPT LINTING SUMMARY');
        console.log('='.repeat(80));
        
        if (this.errors.length === 0) {
            console.log('✅ All JavaScript blocks passed linting successfully!');
        } else {
            console.log(`⚠️  Found ${this.errors.length} block(s) with issues:`);
            this.errors.forEach(error => {
                console.log(`   • Block ${error.block} (lines ${error.lines})`);
            });
        }
        
        console.log('\n💡 Tips for HTML template JavaScript:');
        console.log('   • Avoid inline JavaScript when possible');
        console.log('   • Extract complex JavaScript to separate files');
        console.log('   • Use CSP-safe patterns for dynamic content');
        console.log('   • Consider using data attributes instead of template variables in JS');
    }
}

// Main execution
async function main() {
    const linter = new TemplateJSLinter();
    
    try {
        // Get template file from command line or use default
        const templateFile = process.argv[2] || 'templates/base.html';
        
        if (!fs.existsSync(templateFile)) {
            console.error(`❌ Template file not found: ${templateFile}`);
            process.exit(1);
        }

        console.log('🚀 HTML Template JavaScript Linter');
        console.log('='.repeat(80));
        console.log(`🎯 Target: ${templateFile}\n`);

        await linter.lintTemplate(templateFile);
        linter.printSummary();
        
    } catch (error) {
        console.error('❌ Fatal error:', error.message);
        process.exit(1);
    } finally {
        linter.cleanup();
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { TemplateJSLinter };
