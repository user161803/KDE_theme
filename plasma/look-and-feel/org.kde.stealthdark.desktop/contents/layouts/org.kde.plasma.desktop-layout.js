// Stealth Dark default layout: one floating, centred dock-style panel.
// Applied when "Desktop and window layout" is ticked in System Settings >
// Colors & Themes > Global Theme (Plasma 6) / Global Theme (Plasma 5).
// Works on Plasma 5.25+ and Plasma 6.

function plasmaVersion() {
    var v = (typeof applicationVersion !== "undefined") ? String(applicationVersion) : "6.0";
    var parts = v.split(".");
    return { major: parseInt(parts[0], 10) || 6, minor: parseInt(parts[1], 10) || 0 };
}
var version = plasmaVersion();

var panel = new Panel;
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.4 / 2);
panel.alignment = "center";
panel.hiding = "none";
// Floating panels exist since Plasma 5.25
try { panel.floating = true; } catch (e) { print("floating not supported: " + e); }

if (version.major > 6 || (version.major === 6 && version.minor >= 1)) {
    // Plasma 6.1+: the panel shrinks to fit its widgets
    try { panel.lengthMode = "fit"; } catch (e) { print("lengthMode not supported: " + e); }
} else {
    // Plasma 5 / 6.0: emulate the dock with a fixed, centred length
    var geo = screenGeometry(panel.screen);
    var length = Math.round(Math.min(geo.width * 0.5, gridUnit * 50));
    panel.minimumLength = length;
    panel.maximumLength = length;
}

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
