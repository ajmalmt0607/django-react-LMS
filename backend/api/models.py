import math
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


from userauths.models import User, Profile
from shortuuid.django_fields import ShortUUIDField
from moviepy.editor import VideoFileClip

LANGUAGE = (
    ("English", "English"),
    ("Spanish", "Spanish"),
    ("French", "French"),
)

LEVEL = (
    ("Beginner", "Beginner"),
    ("Intermediate", "Intermediate"),
    ("Advanced", "Advanced"),
)

TEACHER_STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Published", "Published"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", "Failed"),
)

PLATFORM_STATUS = (
    ("Review", "Review"),
    ("Disabled", "Disabled"),
    ("Rejected", "Rejected"),
    ("Draft", "Draft"),
    ("Published", "Published"),
)

RATING = (
    (1, "1 Star"),
    (2, "2 Star"),
    (3, "3 Star"),
    (4, "4 Star"),
    (5, "5 Star"),
)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="default.jpg")
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.full_name
    
    def students(self):
        return CartOrderItem.objects.filter(teacher=self)
    
    def courses(self):
        return Course.objects.filter(teacher=self)

    def review(self):
        return Course.objects.filter(teacher=self).count()


class Category(models.Model):
    title = models.CharField(max_length=100)
    image  = models.FileField(upload_to="course-file", default="category.jpg", null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Category"
        ordering = ["title"]

    def __str__(self):
        return self.title
    
    def course_count(self):
        return Course.objects.filter(category=self).count()
    
    def save(self, *args, **kwargs):# rewriting default save method
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)

class Course(models.Model):
    # when category that is related to a course gets deleted, we dont want to delete the whole course that is (on_delete=models.SET_NULL)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    file = models.FileField(upload_to="course-file", blank=True, null=True)
    image = models.FileField(upload_to="course-file", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    language = models.CharField(choices=LANGUAGE, default="English")
    level = models.CharField(choices=LEVEL, default="Beginner")
    platform_status = models.CharField(choices=PLATFORM_STATUS, default="Published")
    teacher_course_status = models.CharField(choices=TEACHER_STATUS, default="Published")
    featured = models.BooleanField(default=False)
    course_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    slug = models.SlugField(unique=True, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):# rewriting default save method
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)

    def students(self):
        return EnrolledCourse.objects.filter(course=self)
    
    def curriculum(self):
        return VariantItem.objects.filter(variant__course=self)
    
    def lectures(self):
        # Get the variant related to the VariantItem. and Then get the course associated with that variant.
        return VariantItem.objects.filter(variant__course=self)
    
    def average_rating(self):
        # The aggregate() function is used to compute summary statistics over the filtered queryset.
        # models.Avg('rating') is a Django aggregation function that calculates the average value of the rating field for all reviews returned by the filter
        # The result will be a dictionary where the key is avg_rating, and the value is the calculated average. {'avg_rating': 4.0}
        average_rating = Review.objects.filter(course=self, active=True).aggregate(avg_rating=models.Avg('rating'))

    def rating_count(self):
        return Review.objects.filter(course=self, active=True).count()
    
    def reviews(self):
        return Review.objects.filter(course=self, active=True)
    

class Variant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    variant_id = ShortUUIDField(unique=True, Length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
    def variant_items(self):
        return VariantItem.objects.filter(variant=self)
    
class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="variant_items")
    title = models.CharField(max_length=1000)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="course-file")
    duration = models.DurationField(null=True, blank=True)
    content_duration = models.CharField(max_length=1000, null=True, blank=True)
    preview = models.BooleanField(default=False)
    variant_item_id = ShortUUIDField(unique=True, Length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.variant.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds = clip.duration
            
            # divmod is python inbuilt funciton that two numbers as arguments and return tuple containing two values
            minutes, reminder = divmod(duration_seconds, 60) # eg. 3600/60 = 60 is minutes, 0 is reminder
            minutes = math.floor(minutes)
            seconds = math.floor(reminder)

            duration_text = f"{minutes}m {seconds}s" #60m 35s
            self.content_duration = duration_text

            # Here we saying updated field 'content_duration' update during save
            super().save(update_fields=['content_duration'])


class Question_Answer(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['-date']

    def message(self):
        return Question_Answer_Message.objects.filter(question=self)
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Question_Answer_Message(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.ForeignKey(Question_Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    qam_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['date']

    def profile(self):
        return Profile.objects.get(user=self.user)
    

class Cart(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    country = models.CharField(max_length=100, null=True, blank=True)
    cart_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CartOrder(models.Model):
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ManyToManyField(Teacher, blank=True)
    sub_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    payment_status = models.CharField(choices=PAYMENT_STATUS, default="Processing")
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    coupons = models.ManyToManyField("api.Coupon", blank= True)
    stripe_session_id = models.CharField(max_length=1000, null=True, blank=True)
    oid = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def order_items(self):
        # return all the cart order items related to this purticular order
        return CartOrderItem.objects.filter(order=self)
    
    def __str__(self):
        return self.oid
    
class CartOrderItem(models.Model):
    # This ForeignKey links each CartOrderItem to a CartOrder.
    # The related_name="orderitem" defines how you can access all CartOrderItems related to a specific CartOrder object.
    # For example, if you have a CartOrder instance called cart_order, you can get all related CartOrderItems by using:
    # cart_order.orderitem.all()    
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name="orderitem")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="order_item")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    coupons = models.ForeignKey("api.Coupon", on_delete=models.SET_NULL, null=True, blank=True)
    applied_coupon = models.BooleanField(default=False)
    oid = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['-date']

    def order_id(self):
        # return all the cart order items related to this purticular order
        return f"Order ID #{self.order.oid}"

    def payment_status(self):
        return f"{self.order.payment_status}"
    
    def __str__(self):
        return self.oid
    

class Certificate(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    certificate_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CompletedLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    variant_item = models.ForeignKey(VariantItem, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class EnrolledCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.CASCADE)
    enrollment_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.course.title
    
    def lectures(self):
        # return all VariantItem matching with the same course
        return VariantItem.objects.filter(variant__course=self.course)
    
    def completed_lesson(self):
        return CompletedLesson.objects.filter(course=self.course, user=self.user)
    
    def curriculum(self):
        return Variant.objects.filter(course=self.course)
    
    def note(self):
        return Note.objects.filter(course=self.course, user=self.user)
    
    def question_answer(self):
        return Question_Answer.objects.filter(course=self.course)
    
    def review(self):
        return Review.objects.filter(course=self.course, user=self.user).first()


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, null=True, blank=True)
    note = models.TextField()
    note_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    reply = models.CharField(null=True, blank=True, max_length=1000)
    active = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.type   