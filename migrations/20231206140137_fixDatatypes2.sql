alter table Semester_study_groups
    modify semester INT UNSIGNED not null;

alter table Study_groups
    modify color INT UNSIGNED not null;

alter table Tmpc
    modify token INT UNSIGNED not null;
