#!/usr/bin/env python3
import argparse

from billiebot_summary.summary_generator import generate_summary


def main():
    parser = argparse.ArgumentParser(description='Generate a deterministic BillieBot daily summary.')
    parser.add_argument('--database-path', default='~/.billiebot/billiebot_events.sqlite3')
    parser.add_argument('--date', default='', help='YYYY-MM-DD. Defaults to today.')
    parser.add_argument('--output-path', default='~/.billiebot/summaries')
    args = parser.parse_args()
    summary, output_path = generate_summary(args.database_path, args.date, args.output_path)
    print(summary)
    print(f'\nWrote summary to {output_path}')


if __name__ == '__main__':
    main()
