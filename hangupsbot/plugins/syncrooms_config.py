def _initialise(Handlers, bot=None):
    if "register_admin_command" in dir(Handlers) and "register_user_command" in dir(Handlers):
        Handlers.register_admin_command(["attachsyncout", "detachsyncout"])
        return []
    else:
        print("SYNCROOMS_CONFIG: LEGACY FRAMEWORK MODE")
        return ["attachsyncout", "detachsyncout"]


def attachsyncout(bot, event, *args):
    if len(args) <= 0:
        bot.send_message_parsed(event.conv, "<b>Syntax:</b> /bot attachsyncout <conversation_id>")
        return

    conversation_ids = list(args)

    quietly = False
    if "quietly" in conversation_ids:
        quietly = True
        conversation_ids.remove("quietly")

    if len(args) == 1:
        conversation_ids.append(event.conv_id)

    conversation_ids = list(set(conversation_ids))

    if len(conversation_ids) < 2:
        # need at least 2 ids, one has to be another room
        return

    if not bot.get_config_option('syncing_enabled'):
        return

    syncouts = bot.get_config_option('sync_rooms')

    if syncouts is None:
        return

    affected_conversations = None

    found_existing = False
    for sync_room_list in syncouts:
        if any(x in conversation_ids for x in sync_room_list):
            missing_ids = list(set(conversation_ids) - set(sync_room_list))
            sync_room_list.extend(missing_ids)
            affected_conversations = list(sync_room_list) # clone
            found_existing = True
            break

    if not found_existing:
        syncouts.append(conversation_ids)
        affected_conversations = conversation_ids

    if affected_conversations:
        bot.config.set_by_path(["sync_rooms"], syncouts)
        bot.config.save()
        if found_existing:
            print("SYNCROOM_CONFIG: extended")
            html_message = "<i>syncout updated: {} conversations</i>"
        else:
            print("SYNCROOM_CONFIG: created")
            html_message = "<i>syncout created: {} conversations</i>"
    else:
        print("SYNCROOM_CONFIG: no change")
        html_message = "<i>syncouts unchanged</i>"

    if not quietly:
        bot.send_message_parsed(event.conv, html_message.format(
            len(affected_conversations)))


def detachsyncout(bot, event, target_conversation_id=None, *args):
    if not bot.get_config_option('syncing_enabled'):
        return

    syncouts = bot.get_config_option('sync_rooms')

    if not syncouts:
        return

    if target_conversation_id is None:
        # detach myself if no target_conversation_id provided
        target_conversation_id = event.conv_id

    _detached = False
    for sync_room_list in syncouts:
        if target_conversation_id in sync_room_list:
            sync_room_list.remove(target_conversation_id)
            _detached = True
            break;

    # cleanup: remove empty or 1-item syncouts by rewriting variable
    _syncouts = []
    for sync_room_list in syncouts:
        if len(sync_room_list) > 1:
            _syncouts.append(sync_room_list)
    syncouts = _syncouts

    if _detached:
        bot.config.set_by_path(["sync_rooms"], syncouts)
        bot.config.save()
        bot.send_message_parsed(event.conv, "<i>{} was detached</b></i>".format(target_conversation_id))
