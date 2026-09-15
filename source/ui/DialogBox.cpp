#include "ui/DialogBox.h"

#include <stdio.h>

#include "ui/TopTextService.h"

namespace {

constexpr int kMinReadingFrames = 90;
constexpr int kFramesPerCharacter = 3;
constexpr int kMaxReadingFrames = 270;
// A newer message replaces the current one after it was visible this long.
constexpr int kMinShownFrames = 45;

} // namespace

void DialogBox::Fill(Message &message, const char *speaker, const char *text, DialogTask task)
{
    snprintf(message.speaker, sizeof(message.speaker), "%s", speaker);
    snprintf(message.text, sizeof(message.text), "%s", text);
    message.task = task;
}

void DialogBox::Say(const char *speaker, const char *text)
{
    if (count_ > 0)
    {
        // Keep only waiting messages from this very moment.
        int kept = 1;
        for (int i = 1; i < count_; i++)
        {
            const Message &waiting = queue_[(head_ + i) % kQueueSize];
            if (waiting.stamp == frame_)
                queue_[(head_ + kept++) % kQueueSize] = waiting;
        }
        count_ = kept;

        // An older current message makes room soon.
        if (queue_[head_].stamp != frame_)
        {
            int remaining = kMinShownFrames - shown_;
            if (remaining < 0)
                remaining = 0;
            if (timer_ > remaining)
                timer_ = remaining;
        }
    }

    if (count_ >= kQueueSize)
        return;

    Message &message = queue_[(head_ + count_) % kQueueSize];
    Fill(message, speaker, text, DialogTask::None);
    message.stamp = frame_;
    count_++;
    if (count_ == 1)
    {
        timer_ = ReadingFrames(queue_[head_]);
        shown_ = 0;
        dirty_ = true;
    }
}

void DialogBox::Ask(const char *speaker, const char *text, DialogTask task)
{
    Fill(request_, speaker, text, task);
    hasRequest_ = true;
    if (count_ == 0)
        dirty_ = true;
}

void DialogBox::CompleteTask(DialogTask task)
{
    if (hasRequest_ && request_.task == task)
    {
        hasRequest_ = false;
        if (count_ == 0)
            dirty_ = true;
    }
}

void DialogBox::Clear()
{
    count_ = 0;
    hasRequest_ = false;
    dirty_ = true;
}

int DialogBox::ReadingFrames(const Message &message)
{
    int characters = 0;
    for (const char *p = message.text; *p != '\0'; p++)
    {
        if ((static_cast<unsigned char>(*p) & 0xC0) != 0x80)
            characters++;
    }
    int frames = kMinReadingFrames + characters * kFramesPerCharacter;
    return frames > kMaxReadingFrames ? kMaxReadingFrames : frames;
}

void DialogBox::Update(bool skip)
{
    frame_++;
    if (count_ == 0)
        return;

    shown_++;
    timer_--;
    if (timer_ > 0 && !skip)
        return;

    head_ = (head_ + 1) % kQueueSize;
    count_--;
    if (count_ > 0)
        timer_ = ReadingFrames(queue_[head_]);
    shown_ = 0;
    dirty_ = true;
}

const DialogBox::Message *DialogBox::Current() const
{
    if (count_ > 0)
        return &queue_[head_];
    if (hasRequest_)
        return &request_;
    return nullptr;
}

bool DialogBox::Draw(TopTextService &text)
{
    if (!dirty_)
        return false;
    dirty_ = false;

    const Message *message = Current();
    text.ShowPanel(message != nullptr);
    if (message == nullptr)
        return true;

    text.Clear();
    int column = TopTextService::kTextColumn;
    int row = TopTextService::kTextRow;

    text.SetColor(TextColor::Speaker);
    text.Format(column, row, "%s:", message->speaker);

    text.SetColor(TextColor::Ink);
    text.WriteWrapped(column, row + 1, TopTextService::kTextColumns, TopTextService::kTextRows - 1,
                      message->text);
    return true;
}
