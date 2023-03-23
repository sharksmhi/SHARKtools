
def get_root_app(widget):
    while True:
        parent_widget = widget.master
        if not parent_widget:
            return widget
        widget = parent_widget
