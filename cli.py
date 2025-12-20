#!/usr/bin/env python3
"""Command-line interface for the Italian Hymns API."""

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from hymns.service import HymnService
from utils.scraper import HymnScraper


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def scrape_command(args):
    """Handle the scrape command."""
    setup_logging(args.debug)

    scraper = HymnScraper(output_dir=args.output_dir)

    try:
        if args.format == "full" or args.format == "both":
            scraper.save_full_data()

        if args.format == "csv" or args.format == "both":
            scraper.save_simplified_data()

        print(f"Successfully scraped hymns data to {args.output_dir}")

    except Exception as e:
        print(f"Error scraping data: {e}")
        return 1

    return 0


def stats_command(args):
    """Handle the stats command."""
    setup_logging(args.debug)

    try:
        service = HymnService(data_path=args.data_path or settings.get_data_path())
        stats = service.get_stats()

        print("Hymn Collection Statistics:")
        print(f"  Total hymns: {stats['total_hymns']}")
        print(f"  Categories: {stats['categories']}")
        print(f"  Tags: {stats['tags']}")
        print(f"  Sacramento hymns: {stats['sacramento_hymns']}")

        if args.verbose:
            print("\nCategories:")
            for category in service.get_categories():
                print(f"  - {category}")

            print("\nTags:")
            for tag in service.get_tags()[:20]:  # Show first 20 tags
                print(f"  - {tag}")
            if len(service.get_tags()) > 20:
                print(f"  ... and {len(service.get_tags()) - 20} more")

    except Exception as e:
        print(f"Error getting stats: {e}")
        return 1

    return 0


def serve_command(args):
    """Handle the serve command."""
    import uvicorn

    print(f"Starting Italian Hymns API on {args.host}:{args.port}")

    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


def test_command(args):
    """Handle the test command."""
    import subprocess
    import sys

    cmd = ["pytest"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage:
        cmd.extend(["--cov=hymns", "--cov=api", "--cov-report=term-missing"])

    if args.pattern:
        cmd.extend(["-k", args.pattern])

    try:
        result = subprocess.run(cmd, cwd=".", check=False)
        return result.returncode
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")
        return 1


def db_command(args):
    """Handle database commands."""
    from database.database import db_manager
    from database.history_service import HymnHistoryService
    from hymns.service import HymnService

    setup_logging(args.debug)

    if args.action == "init":
        try:
            db_manager.create_tables()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
            return 1

    elif args.action == "reset":
        try:
            db_manager.drop_tables()
            db_manager.create_tables()
            print("Database reset successfully!")
        except Exception as e:
            print(f"Error resetting database: {e}")
            return 1

    elif args.action == "stats":
        try:
            with db_manager.session_scope() as session:
                from database.models import HymnSelection, SelectedHymn, Ward

                ward_count = session.query(Ward).count()
                selection_count = session.query(HymnSelection).count()
                hymn_count = session.query(SelectedHymn).count()

                print("Database Statistics:")
                print(f"  Wards: {ward_count}")
                print(f"  Hymn Selections: {selection_count}")
                print(f"  Total Hymns Selected: {hymn_count}")

                if args.verbose:
                    print("\nWards:")
                    wards = session.query(Ward).all()
                    for ward in wards:
                        selections = len(ward.hymn_selections)
                        print(f"  - {ward.name}: {selections} selections")

        except Exception as e:
            print(f"Error getting database stats: {e}")
            return 1

    return 0


def demo_command(args):
    """Handle demo command - create sample data."""
    import random
    from datetime import datetime, timedelta

    from database.history_service import HymnHistoryService
    from hymns.service import HymnService

    setup_logging(args.debug)

    try:
        hymn_service = HymnService(data_path=settings.get_data_path())
        history_service = HymnHistoryService(hymn_service)

        ward_names = ["Muggio", "Merate", "Cimiano", "Lodi", "Lecco", "Sondrio"]

        print(f"Creating demo data for {len(ward_names)} wards...")

        # Create selections for the past few weeks
        for ward_name in ward_names:
            print(f"Creating selections for {ward_name}...")

            for weeks_ago in range(8, 0, -1):  # 8 weeks ago to 1 week ago
                selection_date = datetime.now() - timedelta(weeks=weeks_ago)

                # Randomly decide if it's prima domenica or festive
                prima_domenica = weeks_ago % 4 == 1  # Every 4th week
                domenica_festiva = False
                tipo_festivita = None

                if weeks_ago <= 2:  # Recent weeks might be festive
                    if random.random() < 0.3:  # 30% chance
                        domenica_festiva = True
                        # Import the enum here
                        from hymns.models import FestivityType

                        tipo_festivita = random.choice(
                            [FestivityType.NATALE, FestivityType.PASQUA]
                        )

                # Get smart hymns (but don't save them automatically)
                hymns = history_service.get_smart_hymns(
                    ward_name=ward_name,
                    prima_domenica=prima_domenica,
                    domenica_festiva=domenica_festiva,
                    tipo_festivita=tipo_festivita,
                    selection_date=selection_date,
                )

                # Save the selection
                history_service.save_selection(
                    ward_name=ward_name,
                    hymns=hymns,
                    prima_domenica=prima_domenica,
                    domenica_festiva=domenica_festiva,
                    tipo_festivita=tipo_festivita,
                    selection_date=selection_date,
                )

                print(f"  Added selection for {selection_date.strftime('%Y-%m-%d')}")

        print("Demo data created successfully!")
        print("You can now test the smart selection with these wards:")
        for ward in ward_names:
            print(f"  - {ward}")

    except Exception as e:
        print(f"Error creating demo data: {e}")
        return 1

    return 0


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Italian Hymns API - Command Line Interface", prog="python cli.py"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape hymns data from the web"
    )
    scrape_parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for scraped data (default: data)",
    )
    scrape_parser.add_argument(
        "--format",
        choices=["full", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )
    scrape_parser.set_defaults(func=scrape_command)

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show hymn collection statistics"
    )
    stats_parser.add_argument(
        "--data-path",
        help=f"Path to hymns data file (default: {settings.get_data_path()})",
    )
    stats_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed statistics"
    )
    stats_parser.set_defaults(func=stats_command)

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--host",
        default=settings.HOST,
        help=f"Host to bind to (default: {settings.HOST})",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port to bind to (default: {settings.PORT})",
    )
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    serve_parser.set_defaults(func=serve_command)

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose test output"
    )
    test_parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage report"
    )
    test_parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    test_parser.set_defaults(func=test_command)

    # Database command
    db_parser = subparsers.add_parser("db", help="Database management")
    db_parser.add_argument(
        "action", choices=["init", "reset", "stats"], help="Database action to perform"
    )
    db_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed information"
    )
    db_parser.set_defaults(func=db_command)

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Create demo data")
    demo_parser.set_defaults(func=demo_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
