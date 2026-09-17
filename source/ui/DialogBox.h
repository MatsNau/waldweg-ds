#pragma once

#include <array>

#include <nds/ndstypes.h>

class TopTextService;

// Something the player is asked to do; the request stays visible until done.
enum class DialogTask : u8
{
    None,
    GiveBasket,
    GiveScarf,
    GiveLantern,
    GiveBell,
};

// Speech in a parchment panel on the top screen. There are deliberately no
// tutorial hints: the player discovers the game through what Mats says.
// - Say: queued in order and advanced automatically after a reading time, or
//   early when the player skips (A / tap on the map). Nothing is dropped
//   silently: while messages are waiting the current one is shortened instead,
//   but every message stays readable for at least kMinShownFrames.
// - Ask: a request tied to a task. It is shown whenever nothing else is queued
//   and disappears as soon as the task is completed.
class DialogBox
{
public:
    void Say(const char *speaker, const char *text);
    void Ask(const char *speaker, const char *text, DialogTask task);
    void CompleteTask(DialogTask task);
    void Clear();

    // skip: the player wants the current queued message to end early.
    void Update(bool skip);

    bool IsShowing() const { return count_ > 0 || hasRequest_; }
    bool HasQueuedMessages() const { return count_ > 0; }

    // True while the current message may be moved on with A.
    bool CanSkip() const { return count_ > 0 && shown_ >= kSkipGraceFrames; }

    // Redraws the panel if needed; returns true if something changed.
    bool Draw(TopTextService &text);

private:
    // The player cannot skip in the first frames of a message, so that a box
    // never just flashes; the badge appears when skipping becomes possible.
    static constexpr int kSkipGraceFrames = 30;

    static constexpr int kQueueSize = 6;
    static constexpr int kSpeakerSize = 16;
    static constexpr int kTextSize = 160;

    struct Message
    {
        char speaker[kSpeakerSize];
        char text[kTextSize];
        DialogTask task;
        u32 stamp; // frame in which it was triggered
    };

    static void Fill(Message &message, const char *speaker, const char *text, DialogTask task);
    static int ReadingFrames(const Message &message);
    const Message *Current() const;

    // Starts showing queue_[head_] with its full reading time.
    void StartCurrent();
    // Cuts the current reading time short because something is waiting.
    void ShortenCurrent();
    // Moves on to the next message (or to the request / nothing).
    void Advance();
    // Throws away the message right behind the current one (queue full).
    void DropOldestWaiting();
    // Throws away waiting messages whose moment has long passed.
    void DropStaleWaiting();

    std::array<Message, kQueueSize> queue_ = {};
    int head_ = 0;
    int count_ = 0;
    int timer_ = 0;
    int shown_ = 0;  // frames the current message has been visible
    u32 frame_ = 0;

    Message request_ = {};
    bool hasRequest_ = false;

    bool dirty_ = true;
};
