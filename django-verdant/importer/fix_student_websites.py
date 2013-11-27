from rca.models import StudentPageContactsWebsite

def run():
    fixed_student_websites = 0

    # Fix student page websites
    for website in StudentPageContactsWebsite.objects.all():
        if not '://' in website.website:
            website.website = 'http://' + website.website
            website.save()
            fixed_student_websites += 1

    print "Fixed " + str(fixed_student_websites) + " student websites"