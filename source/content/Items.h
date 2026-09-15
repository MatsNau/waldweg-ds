#pragma once

#include <nds/ndstypes.h>

// Items in Nina's backpack that she gives to Mats.
enum class ItemId : u8
{
    Basket,
    Scarf,
    Lantern,
    Bell,
    Count,
};

constexpr int kItemCount = static_cast<int>(ItemId::Count);

inline const char *ItemName(ItemId id)
{
    static constexpr const char *kNames[] = { "Korb", "Schal", "Laterne", "Glöckchen" };
    return kNames[static_cast<int>(id)];
}
