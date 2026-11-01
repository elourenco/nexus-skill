#!/usr/bin/env python3
"""Portable entrypoint; keep the sibling nexus_workflow package when copying."""
import sys
from nexus_workflow.cli import main

if __name__ == '__main__':
    sys.exit(main())
