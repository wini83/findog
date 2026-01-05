"""Message templates rendering helpers."""

import jinja2


class Message:
    """Base message renderer using Jinja2 templates.

    Subclasses should define ``TEMPLATE_FILE`` with a path to the template file.
    """

    TEMPLATE_FILE: str | None = None

    def __init__(self):
        template_loader = jinja2.FileSystemLoader(searchpath="./")
        self.template_env = jinja2.Environment(loader=template_loader)
        if not self.TEMPLATE_FILE:
            raise ValueError("TEMPLATE_FILE must be set in subclass of Message")
        self.template = self.template_env.get_template(self.TEMPLATE_FILE)

    def render(self, **kwargs):
        """Render the template with provided keyword arguments."""
        return self.template.render(**kwargs)


class DailyMessage(Message):
    """Daily email message template renderer."""

    TEMPLATE_FILE = './templates/daily.html'
