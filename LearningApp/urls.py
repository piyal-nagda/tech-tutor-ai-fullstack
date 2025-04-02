from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
                     path("StudentLogin.html", views.StudentLogin, name="StudentLogin"),	      
                     path("StudentLoginAction", views.StudentLoginAction, name="StudentLoginAction"),
		     path("FacultyLogin.html", views.FacultyLogin, name="FacultyLogin"),	      
                     path("FacultyLoginAction", views.FacultyLoginAction, name="FacultyLoginAction"),
                     path("SignupAction", views.SignupAction, name="SignupAction"),
                     path("Signup.html", views.Signup, name="Signup"),
                     path("Summary.html", views.Summary, name="Summary"),
	             path("SummaryAction", views.SummaryAction, name="SummaryAction"),	    
		     path("Subjective.html", views.Subjective, name="Subjective"),
	             path("SubjectiveAction", views.SubjectiveAction, name="SubjectiveAction"),	
		     path("ChoiceQuestion.html", views.ChoiceQuestion, name="ChoiceQuestion"),
		     path("ChoiceQuestionAction", views.ChoiceQuestionAction, name="ChoiceQuestionAction"),
		     path("StudentSummary.html", views.StudentSummary, name="StudentSummary"),
	             path("StudentSummaryAction", views.StudentSummaryAction, name="StudentSummaryAction"),
		     path("ViewMarks", views.ViewMarks, name="ViewMarks"),	
		     path("ModelAnalysis", views.ModelAnalysis, name="ModelAnalysis"),	
		     path("WriteExam.html", views.WriteExam, name="WriteExam"),
	             path("WriteExamAction", views.WriteExamAction, name="WriteExamAction"),
		     path("StudentMarks", views.StudentMarks, name="StudentMarks"),	
		     path("ShowQuestions", views.ShowQuestions, name="ShowQuestions"),
		     path("ViewAnswers", views.ViewAnswers, name="ViewAnswers"),	
		     path("ViewAnswersAction", views.ViewAnswersAction, name="ViewAnswersAction"),	
]
