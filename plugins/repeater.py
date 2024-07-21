from botoy import S, ctx, mark_recv, logger, jconfig

group_class = {}


class Repeater:
    def __init__(self, trigger_count):
        self.trigger_count = trigger_count
        self.message_count = 1
        self.sender = []
        self.message = None
        self.previous_message = None

    def receive_message(self, sender, message) -> bool:
        if message == self.previous_message:
            return False
        # if message == self.message and sender not in self.sender:
        if message == self.message:
            self.message_count += 1
            self.sender.append(sender)
        else:
            self.message_count = 1
            self.message = message
            self.sender = []
            return False

        if self.message_count == self.trigger_count:
            self.message_count = 1
            self.sender = []
            self.previous_message = message
            return True


async def main():
    if m := ctx.group_msg:
        if group_class.get(m.from_group):
            if group_class[m.from_group].receive_message(m.from_user, m.text):
                logger.info(f"群[{m.from_group}] 复读:>> {m.text} <<")
                await S.text(m.text)
        else:
            group_class[m.from_group] = Repeater(int(jconfig.get("repeat_after_count")))


mark_recv(main, author='yuban10703', name="复读机", usage='自动复读')
