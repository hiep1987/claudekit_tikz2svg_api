#!/usr/bin/env python3
"""
WCAG Contrast Ratio Checker
Kiểm tra độ tương phản giữa màu text và background theo chuẩn WCAG

Usage:
    python3 check_contrast_ratio.py

Hoặc import trong Python script:
    from check_contrast_ratio import check_contrast, contrast_ratio
    check_contrast("#f5f5f5", "#333", "My Colors")
    
Documentation: CONTRAST_CHECKER_GUIDE.md
"""

def rgb_to_luminance(r, g, b):
    """Convert RGB to relative luminance"""
    def channel_luminance(c):
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)


def contrast_ratio(rgb1, rgb2):
    """Calculate contrast ratio between two RGB colors"""
    l1 = rgb_to_luminance(*rgb1)
    l2 = rgb_to_luminance(*rgb2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        # Expand shorthand (e.g., #fff -> #ffffff)
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def check_contrast(bg_color, text_color, mode_name=""):
    """Check contrast ratio and print results"""
    if isinstance(bg_color, str):
        bg_rgb = hex_to_rgb(bg_color)
    else:
        bg_rgb = bg_color
    
    if isinstance(text_color, str):
        text_rgb = hex_to_rgb(text_color)
    else:
        text_rgb = text_color
    
    ratio = contrast_ratio(bg_rgb, text_rgb)
    
    print(f"{mode_name}:" if mode_name else "Contrast Check:")
    print(f"  Background: {bg_rgb}")
    print(f"  Text: {text_rgb}")
    print(f"  Contrast Ratio: {ratio:.2f}:1")
    print(f"  WCAG AA (≥4.5): {'✅ PASS' if ratio >= 4.5 else '❌ FAIL'}")
    print(f"  WCAG AAA (≥7): {'✅ PASS' if ratio >= 7 else '❌ FAIL'}")
    
    return ratio


def main():
    """Main function - check contrast ratios"""
    print("=" * 60)
    print("WCAG CONTRAST RATIO CHECKER")
    print("=" * 60)
    print()
    
    # Example: Check login modal button contrast
    print("=== Login Modal Cancel Button (var(--text-primary)) ===\n")
    
    # Light Mode
    bg_light = (245, 245, 245)      # #f5f5f5 --bg-secondary (light)
    text_light = (51, 51, 51)       # #333333 --text-primary (light)
    
    ratio_light = check_contrast(bg_light, text_light, "Light Mode")
    
    print()
    
    # Dark Mode
    bg_dark = (42, 42, 42)          # #2a2a2a --bg-secondary (dark)
    text_dark = (229, 229, 229)     # #e5e5e5 --text-primary (dark)
    
    ratio_dark = check_contrast(bg_dark, text_dark, "Dark Mode")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if ratio_light >= 4.5 and ratio_dark >= 4.5:
        print("✅ Both light and dark modes meet WCAG AA standards!")
        print(f"   Light mode: {ratio_light:.2f}:1")
        print(f"   Dark mode: {ratio_dark:.2f}:1")
    else:
        print("⚠️  Some modes still fail WCAG standards")
    print()
    
    # Add more color combinations to check here
    # Example:
    # print("\n=== Custom Color Check ===\n")
    # check_contrast("#ffffff", "#000000", "White bg + Black text")


if __name__ == "__main__":
    main()

