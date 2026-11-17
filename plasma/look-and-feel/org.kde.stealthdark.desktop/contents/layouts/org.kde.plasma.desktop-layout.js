// Stealth Dark default layout: one floating, centred dock-style panel.
// Applied when "Desktop and window layout" is ticked in System Settings >
// Colors & Themes > Global Theme.

var panel = new Panel;
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.4 / 2);
panel.alignment = "center";
panel.hiding = "none";
// Newer Plasma 6 properties; ignored gracefully on releases that lack them
try { panel.floating = true; } catch (e) { print("floating not supported: " + e); }
try { panel.lengthMode = "fit"; } catch (e) { print("lengthMode not supported: " + e); }

var kickoff = panel.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", "start-here-kde-symbolic");
kickoff.currentConfigGroup = ["Shortcuts"];
kickoff.writeConfig("global", "Alt+F1");

panel.addWidget("org.kde.plasma.pager");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:systemsettings.desktop",
    "preferred://filemanager",
    "preferred://browser",
    "applications:org.kde.konsole.desktop"
]);

panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.kde.plasma.systemtray");

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("use24hFormat", "2");

panel.addWidget("org.kde.plasma.showdesktop");

// Wallpaper for every desktop (install.sh puts the package in ~/.local/share)
try {
    var allDesktops = desktops();
    for (var i = 0; i < allDesktops.length; ++i) {
        var d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
        d.writeConfig("Image", "file://" + userDataPath() + "/.local/share/wallpapers/StealthDark/");
    }
} catch (e) {
    print("could not set the wallpaper: " + e);
}
