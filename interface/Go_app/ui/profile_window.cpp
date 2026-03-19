#include "profile_window.h"
#include "ui_profile_window.h"

profile_window::profile_window(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::profile_window)
{
    ui->setupUi(this);
}

profile_window::~profile_window()
{
    delete ui;
}
