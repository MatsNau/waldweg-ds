#include "ui/DialogBox.h"

#include <stdio.h>

#include "ui/TopTextService.h"

namespace {

constexpr int kMinReadingFrames = 90;
constexpr int kFramesPerCharacter = 3;
constexpr int kMaxReadingFrames = 300;
// Every message stays readable this long, even when the next one is waiting.
constexpr int kMinShownFrames = 60;
// While something is waiting, the current message does not linger.
constexpr int kQueuedReadingFrames = 180;
// A message that has been waiting this long is out of context and is dropped
// instead of popping up minutes after what triggered it.
constexpr int kStaleFrames = 900;
} // namespace

void DialogBox::Fill(Message &message, const char *speaker, const char *text, DialogTask task)
{
    snprintf(message.speaker, sizeof(message.speaker), "%s", speaker);
    snprintf(message.text, sizeof(message.text), "%s", text);
    message.task = task;
}

void DialogBox::Say(const char *speaker, const char *text)
{
    if (count_ >= kQueueSize)
        DropOldestWaiting();

    Message &message = queue_[(head_ + count_) % kQueueSize];
    Fill(message, speaker, text, DialogTask::None);
    message.stamp = frame_;
    count_++;

    if (count_ == 1)
        StartCurrent();
    else
        ShortenCurrent();
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
    timer_ = 0;
    shown_ = 0;
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

void DialogBox::StartCurrent()
{
    timer_ = ReadingFrames(queue_[head_]);
    shown_ = 0;
    dirty_ = true;
}

void DialogBox::ShortenCurrent()
{
    int least = kMinShownFrames - shown_;
    if (least < 0)
        least = 0;
    int most = kQueuedReadingFrames - shown_;
    if (most < least)
        most = least;
    if (timer_ > most)
        timer_ = most;
}

void DialogBox::DropOldestWaiting()
{
    if (count_ < 2)
        return;
    for (int i = 1; i + 1 < count_; i++)
        queue_[(head_ + i) % kQueueSize] = queue_[(head_ + i + 1) % kQueueSize];
    count_--;
}

void DialogBox::DropStaleWaiting()
{
    int kept = 1;
    for (int i = 1; i < count_; i++)
    {
        const Message &waiting = queue_[(head_ + i) % kQueueSize];
        if (frame_ - waiting.stamp > static_cast<u32>(kStaleFrames))
            continue;
        if (kept != i)
            queue_[(head_ + kept) % kQueueSize] = waiting;
        kept++;
    }
    count_ = kept;
}

void DialogBox::Advance()
{
    head_ = (head_ + 1) % kQueueSize;
    count_--;
    if (count_ > 0)
    {
        StartCurrent();
        if (count_ > 1)
            ShortenCurrent();
        return;
    }
    timer_ = 0;
    shown_ = 0;
    dirty_ = true;
}

void DialogBox::Update(bool skip)
{
    frame_++;
    if (count_ == 0)
        return;

    shown_++;
    timer_--;
    DropStaleWaiting();

    bool skipped = skip && shown_ >= kSkipGraceFrames;
    if (timer_ > 0 && !skipped)
        return;

    Advance();
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
    // The badge comes and goes without the text changing.
    text.ShowSkipHint(CanSkip());

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
