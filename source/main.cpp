#include "core/Application.h"

int main()
{
    // Static: the game objects are too large for the default stack.
    static Application application;
    application.Run();
}
