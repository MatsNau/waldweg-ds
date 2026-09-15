#include "game/StoryDirector.h"

#include <stdio.h>

#include "entities/Mats.h"
#include "entities/Nina.h"
#include "game/GameProgress.h"
#include "ui/DialogBox.h"
#include "world/TimeOfDayService.h"

namespace {

constexpr const char *kMats = "Mats";
constexpr const char *kNina = "Nina";

constexpr int kScarfGate = 5;
constexpr int kLanternGate = 9;

// The sun sinks with every processed mushroom (night comes with the ritual).
DayPhase PhaseForProcessed(int processed)
{
    if (processed >= kLanternGate)
        return DayPhase::Blue;
    if (processed >= 7)
        return DayPhase::Violet;
    if (processed >= kScarfGate)
        return DayPhase::Rose;
    if (processed >= 3)
        return DayPhase::Amber;
    return DayPhase::Golden;
}

} // namespace

void StoryDirector::Start()
{
    progress_.Reset();
    progress_.Unlock(ItemId::Basket);
    mats_.ClearItems();
    nina_.SetWearingHat(false);
    happyFrames_ = 0;
    worriedFrames_ = 0;
    restartRequested_ = false;
    finaleRequested_ = false;
    services_.timeOfDay.Reset(DayPhase::Golden);

    dialog_.Clear();
    dialog_.Say(kMats, "Puh, wir haben uns echt verlaufen... Aber schau mal, hier wachsen überall Pilze!");
    dialog_.Ask(kMats, "Gibst du mir den Korb aus deinem Rucksack? Dann sammeln wir welche.",
                DialogTask::GiveBasket);
}

void StoryDirector::Update()
{
    if (happyFrames_ > 0)
        happyFrames_--;
    if (worriedFrames_ > 0)
        worriedFrames_--;
}

bool StoryDirector::RequestPick()
{
    if (progress_.CanCarryMore())
        return true;

    dialog_.Say(kMats, "Deine Hände sind ja schon voll! Gib mir doch erst den Korb.");
    return false;
}

void StoryDirector::OnIdentified(SpeciesId actual, SpeciesId chosen)
{
    char line[120];
    const char *name = Species(actual).name;

    if (actual == chosen)
    {
        happyFrames_ = kHappyFrames;
        if (IsPoisonous(actual))
            snprintf(line, sizeof(line), "%s? Gut erkannt. Den lassen wir lieber stehen.", name);
        else
            snprintf(line, sizeof(line), "Ein %s! Der kommt in den Korb.", name);
        dialog_.Say(kMats, line);
    }
    else if (!IsPoisonous(actual))
    {
        // Mixing up edible mushrooms is harmless: it is simply put aside.
        dialog_.Say(kMats, "Hm... da bin ich mir nicht so sicher. Den legen wir lieber weg.");
    }
    else
    {
        progress_.AddMistake();
        worriedFrames_ = kWorriedFrames;
        if (progress_.Mistakes() > GameProgress::kFreeMistakes)
        {
            dialog_.Say(kMats, "Mir ist ganz flau im Magen... Komm, wir fangen nochmal von vorn an.");
            restartRequested_ = true;
            return;
        }
        dialog_.Say(kMats, "Warte! Der sieht mir gar nicht geheuer aus. Den werfen wir lieber weg.");
    }

    OnMushroomProcessed();
}

void StoryDirector::OnMushroomProcessed()
{
    progress_.AddProcessed();
    int processed = progress_.Processed();
    services_.timeOfDay.BlendTo(PhaseForProcessed(processed));

    if (processed == kScarfGate)
    {
        progress_.Unlock(ItemId::Scarf);
        dialog_.Ask(kMats, "Brrr... die Sonne geht unter, und mir wird kalt. Hast du meinen Schal dabei?",
                    DialogTask::GiveScarf);
    }
    else if (processed == kLanternGate)
    {
        progress_.Unlock(ItemId::Lantern);
        dialog_.Ask(kMats, "Es wird dunkel. Gib mir die Laterne, dann leuchte ich uns den Weg!",
                    DialogTask::GiveLantern);
    }
}

void StoryDirector::OnItemGiven(ItemId item)
{
    progress_.Give(item);
    mats_.ShowItem(item);
    happyFrames_ = kHappyFrames;

    switch (item)
    {
        case ItemId::Basket:
            dialog_.CompleteTask(DialogTask::GiveBasket);
            dialog_.Say(kMats, "Danke! Ich trage den Korb, und du suchst die Pilze.");
            break;
        case ItemId::Scarf:
            dialog_.CompleteTask(DialogTask::GiveScarf);
            nina_.SetWearingHat(true);
            dialog_.Say(kMats, "Ahh, schön warm. Danke dir!");
            dialog_.Say(kNina, "Dann setze ich meine Mütze auch auf.");
            break;
        case ItemId::Lantern:
            dialog_.CompleteTask(DialogTask::GiveLantern);
            dialog_.Say(kMats, "So sieht man wieder was. Da hinten glimmt doch etwas...?");
            break;
        case ItemId::Bell:
            dialog_.CompleteTask(DialogTask::GiveBell);
            dialog_.Say(kMats, "Kling... kling... kling...");
            finaleRequested_ = true;
            break;
        case ItemId::Count:
            break;
    }
}

bool StoryDirector::ConsumeFinaleRequest()
{
    bool requested = finaleRequested_;
    finaleRequested_ = false;
    return requested;
}

void StoryDirector::OnNearShrine()
{
    if (progress_.WasShrineIntroShown() || progress_.HasOffering())
        return;

    progress_.MarkShrineIntroShown();
    dialog_.Say(kMats, "Ein alter Schrein, mitten im Wald... Auf dem Stein fehlt irgendwas, oder?");
    dialog_.Say(kNina, "Vielleicht finden wir noch, was hierher gehört.");
}

void StoryDirector::OnOfferingTaken()
{
    progress_.TakeOffering();
    dialog_.Say(kNina, "Der leuchtet ja wie ein kleiner Mond... Den nehme ich mit.");
}

bool StoryDirector::OnShrineTapped()
{
    if (!progress_.HasOffering() || progress_.IsOfferingPlaced())
        return false;

    progress_.PlaceOffering();
    progress_.Unlock(ItemId::Bell);
    happyFrames_ = kHappyFrames;
    dialog_.Say(kMats, "Schau, wie er auf dem Stein leuchtet!");
    dialog_.Ask(kMats, "Hörst du das? Das Glöckchen in deinem Rucksack summt ganz leise. Gib es mir mal!",
                DialogTask::GiveBell);
    return true;
}

#ifdef WALDWEG_DEBUG
void StoryDirector::DebugSkipToLantern()
{
    for (ItemId item : { ItemId::Basket, ItemId::Scarf, ItemId::Lantern })
    {
        progress_.Unlock(item);
        progress_.Give(item);
        mats_.ShowItem(item);
    }
    nina_.SetWearingHat(true);
    services_.timeOfDay.BlendTo(DayPhase::Blue);
    dialog_.Clear();
}
#endif

MatsMood StoryDirector::Mood() const
{
    if (worriedFrames_ > 0)
        return MatsMood::Worried;
    if (happyFrames_ > 0)
        return MatsMood::Happy;
    if (progress_.IsUnlocked(ItemId::Scarf) && !progress_.IsGiven(ItemId::Scarf))
        return MatsMood::Cold;
    return MatsMood::Normal;
}
