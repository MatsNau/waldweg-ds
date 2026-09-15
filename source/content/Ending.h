#pragma once

// The final picture: Nina, Mats and Shroomchen sit on a hill at sunrise and
// look at their village in the distance.
namespace ending {

struct Line
{
    const char *speaker;
    const char *text;
};

constexpr Line kDialog[] = {
    { "Mats", "Guck mal, da hinten ist unser Dorf!" },
    { "Nina", "Ja, stimmt. Aber lass uns noch ein bisschen hier bleiben." },
};

constexpr int kDialogLines = sizeof(kDialog) / sizeof(kDialog[0]);

} // namespace ending
