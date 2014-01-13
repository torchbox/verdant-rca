from rca.models import StudentPage

def run():
    fixed_student_websites = 0

    # Fix student page websites
    for student_page in StudentPage.objects.all():
        # Fix in live version of the page
        for website in student_page.website.all():
            if not '://' in website.website:
                website.website = 'http://' + website.website
                website.save()
                fixed_student_websites += 1

        # Fix in latest revision of the page
        student_latest_revision = student_page.get_latest_revision_as_page()
        for website in student_latest_revision.website.all():
            if not '://' in website.website:
                website.website = 'http://' + website.website
                fixed_student_websites += 1
        student_latest_revision.save_revision()

    print "Fixed " + str(fixed_student_websites) + " student websites"