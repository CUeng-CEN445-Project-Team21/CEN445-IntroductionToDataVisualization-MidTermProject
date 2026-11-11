"""
One file per chart. Every chart module exposes:

    build(df) -> plotly Figure    # pure: data in, figure out
    render(df)                    # draws it on the page (and any chart-specific widgets)

To add a chart: copy an existing file, change build(), then add it to src/ui/layout.py.
Widgets inside render() need a unique key, e.g. key="<file name>_<widget>".
"""
