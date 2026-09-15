#pragma once

#include <nds/ndstypes.h>

#include "content/Items.h"

// Everything a restart resets: processed mushrooms, mistakes, items.
class GameProgress
{
public:
    // Without the basket Nina can only carry this many mushrooms.
    static constexpr int kPicksWithoutBasket = 2;
    static constexpr int kFreeMistakes = 3;

    void Reset() { *this = GameProgress(); }

    int Processed() const { return processed_; }
    void AddProcessed() { processed_++; }

    int Mistakes() const { return mistakes_; }
    void AddMistake() { mistakes_++; }

    bool IsUnlocked(ItemId item) const { return (unlocked_ & Bit(item)) != 0; }
    void Unlock(ItemId item) { unlocked_ |= Bit(item); }

    bool IsGiven(ItemId item) const { return (given_ & Bit(item)) != 0; }
    void Give(ItemId item) { given_ |= Bit(item); }

    // The forest-god mushroom: found, then placed on the shrine as an offering.
    bool HasOffering() const { return hasOffering_; }
    void TakeOffering() { hasOffering_ = true; }
    bool IsOfferingPlaced() const { return offeringPlaced_; }
    void PlaceOffering() { offeringPlaced_ = true; }

    bool WasShrineIntroShown() const { return shrineIntroShown_; }
    void MarkShrineIntroShown() { shrineIntroShown_ = true; }

    bool CanCarryMore() const
    {
        return IsGiven(ItemId::Basket) || processed_ < kPicksWithoutBasket;
    }

private:
    static constexpr u8 Bit(ItemId item) { return static_cast<u8>(1 << static_cast<int>(item)); }

    int processed_ = 0;
    int mistakes_ = 0;
    u8 unlocked_ = 0;
    u8 given_ = 0;
    bool hasOffering_ = false;
    bool offeringPlaced_ = false;
    bool shrineIntroShown_ = false;
};
