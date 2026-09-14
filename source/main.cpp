#include <stdio.h>

#include <filesystem.h>
#include <nds.h>
#include <NEMain.h>
#include <nf_lib.h>

#include "ui/text_de.h"

namespace {

constexpr int kSubScreen = 1;
constexpr u32 kTextLayer = 0;

constexpr u32 kPolyIdGround = 0;
constexpr u32 kPolyIdTree = 8;
constexpr u32 kPolyIdMushroom = 16;

struct TimeOfDay
{
    const char *name;
    u32 sky;
    u32 light;
    u32 ambient;
    u32 outline;
};

const TimeOfDay kTimesOfDay[] = {
    { "Goldene Stunde", RGB15(30, 21, 12), RGB15(31, 27, 20), RGB15(13, 10, 8), RGB15(7, 4, 3) },
    { "Abendrot", RGB15(27, 15, 13), RGB15(30, 20, 17), RGB15(11, 8, 9), RGB15(6, 3, 3) },
    { "Dämmerung", RGB15(13, 11, 19), RGB15(18, 16, 24), RGB15(8, 7, 11), RGB15(3, 2, 6) },
    { "Nacht", RGB15(3, 4, 8), RGB15(8, 10, 16), RGB15(5, 5, 8), RGB15(1, 1, 4) },
};
constexpr int kTimeOfDayCount = sizeof(kTimesOfDay) / sizeof(kTimesOfDay[0]);

struct Scene
{
    NE_Camera *camera;
    NE_Material *palette;
    NE_Model *ground;
    NE_Model *tree;
    NE_Model *mushroom;
    int cameraAngle;
    int timeOfDay;
    int fogDepth;
};

struct Placement
{
    float x, z;
    int rotY;
};

const Placement kTrees[] = {
    { -2.2f, -1.6f, 0 }, { 1.9f, -2.3f, 120 }, { 2.6f, 1.2f, 300 }, { -2.8f, 1.8f, 60 },
};
const Placement kMushrooms[] = {
    { 0.4f, 0.3f, 0 }, { -0.7f, -0.4f, 80 }, { 0.9f, -0.9f, 200 },
};

[[noreturn]] void Fail(const char *message)
{
    consoleDemoInit();
    printf("%s\n", message);
    while (true)
        swiWaitForVBlank();
}

void Draw3D(void *arg)
{
    Scene *scene = static_cast<Scene *>(arg);
    NE_CameraUse(scene->camera);

    const auto fog = static_cast<NE_OtherFormatEnum>(NE_FOG_ENABLE);

    NE_PolyFormat(31, kPolyIdGround, NE_LIGHT_0, NE_CULL_BACK, fog);
    NE_ModelDraw(scene->ground);

    NE_PolyFormat(31, kPolyIdTree, NE_LIGHT_0, NE_CULL_BACK, fog);
    for (const Placement &p : kTrees)
    {
        NE_ModelSetCoord(scene->tree, p.x, 0, p.z);
        NE_ModelSetRot(scene->tree, 0, p.rotY, 0);
        NE_ModelDraw(scene->tree);
    }

    NE_PolyFormat(31, kPolyIdMushroom, NE_LIGHT_0, NE_CULL_BACK, fog);
    for (const Placement &p : kMushrooms)
    {
        NE_ModelSetCoord(scene->mushroom, p.x, 0, p.z);
        NE_ModelSetRot(scene->mushroom, 0, p.rotY, 0);
        NE_ModelDraw(scene->mushroom);
    }
}

void UpdateCamera(Scene *scene)
{
    constexpr int radius = floattof32(6.0);
    int x = (sinLerp(scene->cameraAngle) * radius) >> 12;
    int z = (cosLerp(scene->cameraAngle) * radius) >> 12;
    NE_CameraSetI(scene->camera,
                  x, floattof32(3.2), z,
                  0, floattof32(0.6), 0,
                  0, inttof32(1), 0);
}

void ApplyTimeOfDay(Scene *scene)
{
    const TimeOfDay &t = kTimesOfDay[scene->timeOfDay];

    NE_ClearColorSet(t.sky, 31, 63);
    NE_LightSet(0, t.light, -0.6, -0.5, -0.6);
    NE_MaterialSetProperties(scene->palette,
                             RGB15(31, 31, 31), t.ambient,
                             RGB15(0, 0, 0), RGB15(0, 0, 0),
                             false, false);
    NE_FogEnable(5, t.sky, 31, 2, scene->fogDepth);
    for (u32 i = 0; i < 8; i++)
        NE_OutliningSetColor(i, t.outline);
}

void Load3D(Scene *scene)
{
    NE_Init3D();
    // NFLib uses VRAM C/D (sub screen), so textures may only use A/B.
    NE_TextureSystemReset(0, 0, NE_VRAM_AB);

    scene->camera = NE_CameraCreate();
    scene->palette = NE_MaterialCreate();
    scene->ground = NE_ModelCreate(NE_Static);
    scene->tree = NE_ModelCreate(NE_Static);
    scene->mushroom = NE_ModelCreate(NE_Static);

    if (NE_MaterialTexLoadGRF(scene->palette, NULL, NE_TEXGEN_TEXCOORD,
                              "textures/palette.grf") == 0)
        Fail("Textur fehlt: textures/palette.grf");
    if (NE_ModelLoadStaticMeshFAT(scene->ground, "models/ground.bin") == 0)
        Fail("Modell fehlt: models/ground.bin");
    if (NE_ModelLoadStaticMeshFAT(scene->tree, "models/tree.bin") == 0)
        Fail("Modell fehlt: models/tree.bin");
    if (NE_ModelLoadStaticMeshFAT(scene->mushroom, "models/fliegenpilz.bin") == 0)
        Fail("Modell fehlt: models/fliegenpilz.bin");

    NE_ModelSetMaterial(scene->ground, scene->palette);
    NE_ModelSetMaterial(scene->tree, scene->palette);
    NE_ModelSetMaterial(scene->mushroom, scene->palette);

    NE_FogEnableBackground(true);
    NE_OutliningEnable(true);

    ApplyTimeOfDay(scene);
    UpdateCamera(scene);
}

void Load2D()
{
    NF_Set2D(kSubScreen, 0);
    NF_InitTiledBgBuffers();
    NF_InitTiledBgSys(kSubScreen);
    NF_InitTextSys(kSubScreen);

    NF_LoadTextFont("fnt/default", "normal", 256, 256, 0);
    NF_CreateTextLayer(kSubScreen, kTextLayer, 0, "normal");

    setBackdropColorSub(RGB15(6, 4, 3));
}

void DrawInfo(const Scene &scene, int polygons)
{
    char line[64];

    NF_ClearTextLayer(kSubScreen, kTextLayer);
    TextDE_Write(kSubScreen, kTextLayer, 1, 1, "Der Weg aus dem Wald");
    TextDE_Write(kSubScreen, kTextLayer, 1, 2, "Technik-Test – Tag 1");
    TextDE_Write(kSubScreen, kTextLayer, 1, 4, "Umlaute: äöü ÄÖÜ ß");
    TextDE_Write(kSubScreen, kTextLayer, 1, 5, "„Grüner Knollenblätterpilz“");
    TextDE_Write(kSubScreen, kTextLayer, 1, 6, "Überraschung für Nina & Mats");

    TextDE_Write(kSubScreen, kTextLayer, 1, 9, "Steuerkreuz: Kamera drehen");
    TextDE_Write(kSubScreen, kTextLayer, 1, 10, "A: Tageszeit wechseln");
    TextDE_Write(kSubScreen, kTextLayer, 1, 11, "L/R: Nebel-Entfernung");

    snprintf(line, sizeof(line), "Zeit: %s", kTimesOfDay[scene.timeOfDay].name);
    TextDE_Write(kSubScreen, kTextLayer, 1, 14, line);
    snprintf(line, sizeof(line), "Nebel: 0x%04X", scene.fogDepth);
    TextDE_Write(kSubScreen, kTextLayer, 1, 15, line);
    snprintf(line, sizeof(line), "Polygone: %d", polygons);
    TextDE_Write(kSubScreen, kTextLayer, 1, 16, line);

    NF_UpdateTextLayers();
}

} // namespace

int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    NF_Set2D(0, 0);
    NF_Set2D(kSubScreen, 0);

    if (!nitroFSInit(NULL))
        Fail("NitroFS konnte nicht gestartet werden.");

    NF_SetRootFolder("NITROFS");

    irqEnable(IRQ_HBLANK);
    irqSet(IRQ_VBLANK, NE_VBLFunc);
    irqSet(IRQ_HBLANK, NE_HBLFunc);

    Scene scene = {};
    scene.fogDepth = 0x7E00;

    Load3D(&scene);
    Load2D();

    bool infoDirty = true;
    int frame = 0;

    while (true)
    {
        NE_WaitForVBL(static_cast<NE_UpdateFlags>(0));

        if (infoDirty || (frame % 30) == 0)
        {
            DrawInfo(scene, NE_GetPolygonCount());
            infoDirty = false;
        }

        scanKeys();
        u32 held = keysHeld();
        u32 down = keysDown();

        if (held & KEY_LEFT)
        {
            scene.cameraAngle -= 180;
            UpdateCamera(&scene);
        }
        if (held & KEY_RIGHT)
        {
            scene.cameraAngle += 180;
            UpdateCamera(&scene);
        }
        if (down & KEY_A)
        {
            scene.timeOfDay = (scene.timeOfDay + 1) % kTimeOfDayCount;
            ApplyTimeOfDay(&scene);
            infoDirty = true;
        }
        if (held & (KEY_L | KEY_R))
        {
            scene.fogDepth += (held & KEY_R) ? 0x10 : -0x10;
            if (scene.fogDepth < 0x7000)
                scene.fogDepth = 0x7000;
            if (scene.fogDepth > 0x7FFF)
                scene.fogDepth = 0x7FFF;
            ApplyTimeOfDay(&scene);
        }

        NE_ProcessArg(Draw3D, &scene);
        frame++;
    }
}
