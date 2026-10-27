class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def show_info(self):
        print("Нэр:", self.name)
        print("Нас:", self.age)


class GraduateStudent(Student):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

    def show_grade(self):
        print("Анги:", self.grade)


student1 = GraduateStudent("Бат", 18, "12А")

student1.show_info()
student1.show_grade()