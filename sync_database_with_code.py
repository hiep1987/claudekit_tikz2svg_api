#!/usr/bin/env python3
"""
🔄 DATABASE-CODE SYNC SCRIPT
===========================
Synchronizes supported_packages database with SAFE_* sets from app.py
Direction: Update DATABASE → Match CODE (Option 1)

This script ensures:
✅ Database only shows packages that actually work in compilation
✅ No compilation failures from unsupported packages
✅ All working packages are visible to users
"""

import mysql.connector
import sys
from datetime import datetime

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'hiep1987',
    'password': '96445454',
    'database': 'tikz2svg_local',
    'charset': 'utf8mb4'
}

# SAFE PACKAGES FROM app.py CODE (Source of Truth)
SAFE_PACKAGES = {
    'fontspec', 'polyglossia', 'xcolor', 'graphicx', 'geometry', 'setspace',
    'amsmath', 'amssymb', 'amsfonts', 'mathtools', 'physics', 'siunitx', 'cancel', 'cases',
    'tikz', 'pgfplots', 'tikz-3dplot', 'tkz-euclide', 'tkz-tab', 'pgf', 'pgfkeys', 'pgfornament',
    'circuitikz', 'tikz-timing', 'tikz-cd', 'tikz-network', 'tikzpeople', 'tikzmark',
    'array', 'booktabs', 'multirow', 'colortbl', 'longtable', 'tabularx'
}

SAFE_TIKZ_LIBS = {
    'calc','math','positioning','arrows.meta','intersections','angles','quotes',
    'decorations.markings','decorations.pathreplacing','decorations.text',
    'patterns','patterns.meta','shadings','hobby','spy','backgrounds',
    'shapes.geometric','shapes.symbols','shapes.arrows','shapes.multipart',
    'fit','matrix','chains','automata','petri','mindmap','trees',
    'graphs','graphdrawing','lindenmayersystems','fadings','shadows',
    'external','datavisualization','datavisualization.formats.files',
    'datavisualization.formats.files.csv','datavisualization.formats.files.json'
}

SAFE_PGFPLOTS_LIBS = {
    'polar','statistics','dateplot','fillbetween','colorbrewer',
    'groupplots','ternary','smithchart','units'
}

def connect_database():
    """Connect to the database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def get_current_database_packages(cursor):
    """Get current packages from database grouped by type"""
    cursor.execute('SELECT package_name, package_type FROM supported_packages ORDER BY package_type, package_name')
    packages = cursor.fetchall()
    
    db_latex = set()
    db_tikz = set()
    db_pgfplots = set()
    
    for pkg in packages:
        if pkg['package_type'] == 'latex_package':
            db_latex.add(pkg['package_name'])
        elif pkg['package_type'] == 'tikz_library':
            db_tikz.add(pkg['package_name'])
        elif pkg['package_type'] == 'pgfplots_library':
            db_pgfplots.add(pkg['package_name'])
    
    return db_latex, db_tikz, db_pgfplots

def analyze_differences():
    """Analyze differences between database and code"""
    print("\n🔍 ANALYZING CURRENT STATE...")
    print("="*50)
    
    conn = connect_database()
    cursor = conn.cursor(dictionary=True)
    
    db_latex, db_tikz, db_pgfplots = get_current_database_packages(cursor)
    
    # Calculate differences
    latex_to_remove = db_latex - SAFE_PACKAGES
    latex_to_add = SAFE_PACKAGES - db_latex
    
    tikz_to_remove = db_tikz - SAFE_TIKZ_LIBS
    tikz_to_add = SAFE_TIKZ_LIBS - db_tikz
    
    pgfplots_to_remove = db_pgfplots - SAFE_PGFPLOTS_LIBS
    pgfplots_to_add = SAFE_PGFPLOTS_LIBS - db_pgfplots
    
    cursor.close()
    conn.close()
    
    return {
        'latex_remove': latex_to_remove,
        'latex_add': latex_to_add,
        'tikz_remove': tikz_to_remove,
        'tikz_add': tikz_to_add,
        'pgfplots_remove': pgfplots_to_remove,
        'pgfplots_add': pgfplots_to_add
    }

def print_sync_plan(changes):
    """Print what will be changed"""
    print("\n📋 SYNC PLAN - DATABASE → CODE")
    print("="*50)
    
    # LaTeX Packages
    if changes['latex_remove']:
        print(f"\n❌ REMOVE LaTeX Packages ({len(changes['latex_remove'])}):")
        for i, pkg in enumerate(sorted(changes['latex_remove']), 1):
            print(f"   {i:2d}. {pkg}")
    
    if changes['latex_add']:
        print(f"\n➕ ADD LaTeX Packages ({len(changes['latex_add'])}):")
        for i, pkg in enumerate(sorted(changes['latex_add']), 1):
            print(f"   {i:2d}. {pkg}")
    
    # TikZ Libraries
    if changes['tikz_remove']:
        print(f"\n❌ REMOVE TikZ Libraries ({len(changes['tikz_remove'])}):")
        for i, lib in enumerate(sorted(changes['tikz_remove']), 1):
            print(f"   {i:2d}. {lib}")
    
    if changes['tikz_add']:
        print(f"\n➕ ADD TikZ Libraries ({len(changes['tikz_add'])}):")
        for i, lib in enumerate(sorted(changes['tikz_add']), 1):
            print(f"   {i:2d}. {lib}")
    
    # PGFPlots Libraries
    if changes['pgfplots_remove']:
        print(f"\n❌ REMOVE PGFPlots Libraries ({len(changes['pgfplots_remove'])}):")
        for i, lib in enumerate(sorted(changes['pgfplots_remove']), 1):
            print(f"   {i:2d}. {lib}")
    
    if changes['pgfplots_add']:
        print(f"\n➕ ADD PGFPlots Libraries ({len(changes['pgfplots_add'])}):")
        for i, lib in enumerate(sorted(changes['pgfplots_add']), 1):
            print(f"   {i:2d}. {lib}")
    
    total_changes = sum(len(changes[key]) for key in changes.keys())
    print(f"\n📊 TOTAL CHANGES: {total_changes}")
    
    return total_changes

def execute_sync(changes, dry_run=True):
    """Execute the database sync"""
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No changes will be made")
        return True
    
    print(f"\n🚀 EXECUTING DATABASE SYNC...")
    print("="*40)
    
    conn = connect_database()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Remove packages not in code
        packages_to_remove = list(changes['latex_remove']) + list(changes['tikz_remove']) + list(changes['pgfplots_remove'])
        if packages_to_remove:
            print(f"\n❌ Removing {len(packages_to_remove)} packages...")
            for pkg_name in packages_to_remove:
                cursor.execute("DELETE FROM supported_packages WHERE package_name = %s", (pkg_name,))
                print(f"   ❌ Removed: {pkg_name}")
        
        # Add LaTeX packages
        if changes['latex_add']:
            print(f"\n➕ Adding {len(changes['latex_add'])} LaTeX packages...")
            for pkg_name in changes['latex_add']:
                cursor.execute("""
                    INSERT IGNORE INTO supported_packages 
                    (package_name, package_type, description, status)
                    VALUES (%s, 'latex_package', %s, 'active')
                """, (pkg_name, f"LaTeX package: {pkg_name}"))
                print(f"   ➕ Added: {pkg_name}")
        
        # Add TikZ libraries
        if changes['tikz_add']:
            print(f"\n➕ Adding {len(changes['tikz_add'])} TikZ libraries...")
            for lib_name in changes['tikz_add']:
                cursor.execute("""
                    INSERT IGNORE INTO supported_packages 
                    (package_name, package_type, description, status)
                    VALUES (%s, 'tikz_library', %s, 'active')
                """, (lib_name, f"TikZ library: {lib_name}"))
                print(f"   ➕ Added: {lib_name}")
        
        # Add PGFPlots libraries
        if changes['pgfplots_add']:
            print(f"\n➕ Adding {len(changes['pgfplots_add'])} PGFPlots libraries...")
            for lib_name in changes['pgfplots_add']:
                cursor.execute("""
                    INSERT IGNORE INTO supported_packages 
                    (package_name, package_type, description, status)
                    VALUES (%s, 'pgfplots_library', %s, 'active')
                """, (lib_name, f"PGFPlots library: {lib_name}"))
                print(f"   ➕ Added: {lib_name}")
        
        # Log the sync to changelog
        cursor.execute("""
            INSERT INTO package_changelog 
            (package_name, action_type, new_values, changed_by_email, change_reason)
            VALUES ('SYSTEM_SYNC', 'updated', %s, 'admin@tikz2svg.com', 'Database-Code sync: Updated DB to match SAFE_* sets')
        """, (f"Synced at {datetime.now().isoformat()}",))
        
        # Commit transaction
        conn.commit()
        print(f"\n✅ DATABASE SYNC COMPLETED SUCCESSFULLY!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ SYNC FAILED: {e}")
        cursor.close()
        conn.close()
        return False

def verify_sync():
    """Verify the sync was successful"""
    print(f"\n🔍 VERIFYING SYNC RESULTS...")
    print("="*35)
    
    conn = connect_database()
    cursor = conn.cursor(dictionary=True)
    
    db_latex, db_tikz, db_pgfplots = get_current_database_packages(cursor)
    
    # Check if everything matches
    latex_match = db_latex == SAFE_PACKAGES
    tikz_match = db_tikz == SAFE_TIKZ_LIBS
    pgfplots_match = db_pgfplots == SAFE_PGFPLOTS_LIBS
    
    print(f"📦 LaTeX Packages: {'✅ SYNCED' if latex_match else '❌ MISMATCH'}")
    print(f"   Database: {len(db_latex)} | Code: {len(SAFE_PACKAGES)}")
    
    print(f"📚 TikZ Libraries: {'✅ SYNCED' if tikz_match else '❌ MISMATCH'}")  
    print(f"   Database: {len(db_tikz)} | Code: {len(SAFE_TIKZ_LIBS)}")
    
    print(f"📊 PGFPlots Libraries: {'✅ SYNCED' if pgfplots_match else '❌ MISMATCH'}")
    print(f"   Database: {len(db_pgfplots)} | Code: {len(SAFE_PGFPLOTS_LIBS)}")
    
    total_db = len(db_latex) + len(db_tikz) + len(db_pgfplots)
    total_code = len(SAFE_PACKAGES) + len(SAFE_TIKZ_LIBS) + len(SAFE_PGFPLOTS_LIBS)
    
    print(f"\n📊 TOTAL: Database={total_db} | Code={total_code}")
    
    all_synced = latex_match and tikz_match and pgfplots_match
    if all_synced:
        print(f"\n🎉 PERFECT SYNC ACHIEVED! Database matches code exactly.")
    else:
        print(f"\n⚠️ Sync incomplete. Manual review needed.")
    
    cursor.close()
    conn.close()
    return all_synced

def main():
    """Main execution function"""
    print("🔄 DATABASE-CODE SYNC SCRIPT")
    print("="*40)
    print(f"Direction: UPDATE DATABASE → MATCH CODE")
    print(f"Target: SAFE_* sets from app.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Analyze differences
    changes = analyze_differences()
    
    # Step 2: Show sync plan
    total_changes = print_sync_plan(changes)
    
    if total_changes == 0:
        print(f"\n✅ NO CHANGES NEEDED - Database already matches code!")
        return
    
    # Step 3: Confirm execution
    print(f"\n❓ Do you want to proceed with these changes?")
    print(f"⚠️  This will modify the database permanently.")
    
    # For script execution, we'll do a dry run first, then ask for confirmation
    print(f"\n🔍 PERFORMING DRY RUN...")
    execute_sync(changes, dry_run=True)
    
    response = input(f"\n🤔 Execute sync? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        success = execute_sync(changes, dry_run=False)
        if success:
            verify_sync()
    else:
        print(f"\n❌ Sync cancelled by user.")

if __name__ == "__main__":
    main()
