#ifndef PROFILE_WINDOW_H
#define PROFILE_WINDOW_H

#include <QDialog>

namespace Ui {
class profile_window;
}

class profile_window : public QDialog
{
    Q_OBJECT

public:
    explicit profile_window(QWidget *parent = nullptr);
    ~profile_window();

private:
    Ui::profile_window *ui;
};

#endif // PROFILE_WINDOW_H
