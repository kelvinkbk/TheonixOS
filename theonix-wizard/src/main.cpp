#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QIcon>
#include <QFile>

int main(int argc, char *argv[])
{
    // Theonix Wizard runs on first boot to configure user preferences.
    // If the firstboot marker is missing, it silently exits.
    if (!QFile::exists("/etc/theonix/firstboot")) {
        return 0;
    }

    QGuiApplication app(argc, argv);

    // Apply Theonix branding
    app.setOrganizationName("Theonix OS");
    app.setOrganizationDomain("theonix.org");
    app.setApplicationName("Theonix Wizard");
    QIcon::setThemeName("Papirus-Dark");
    
    // Enforce Material style as a baseline for custom QML
    QQuickStyle::setStyle("Material");

    QQmlApplicationEngine engine;
    const QUrl url(QStringLiteral("qrc:/qml/main.qml"));
    
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
        &app, [url](QObject *obj, const QUrl &objUrl) {
            if (!obj && url == objUrl)
                QCoreApplication::exit(-1);
        }, Qt::QueuedConnection);
        
    engine.load(url);

    return app.exec();
}
