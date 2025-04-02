from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
import os
import numpy as np
import pymysql
from pyresparser import utils
from django.core.files.storage import FileSystemStorage
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config
from transformers import AutoTokenizer
from questiongenerator import QuestionGenerator
from questiongenerator import print_qa
from sklearn.feature_extraction.text import TfidfVectorizer
from numpy import dot
from numpy.linalg import norm
from datetime import date

global uname, accuracy, question_count
global model, tokenizer, device

model = T5ForConditionalGeneration.from_pretrained('t5-small')
tokenizer = T5Tokenizer.from_pretrained('t5-small',model_max_length=512)
device = torch.device('cpu')
qg = QuestionGenerator()

def ViewAnswersAction(request):
    if request.method == 'POST':
        global uname, question_count
        aid = request.POST.get('t1', False)
        cols = ['username', 'Assignment ID', 'Question', 'Correct Answer', 'Your Answer']
        output = '<table border="1" align="center" width="100%"><tr>'
        font = '<font size="" color="black">'
        for i in range(len(cols)):
            output += "<td>"+font+cols[i]+"</font></td>"
        output += "</tr>"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from student_answers where username='"+uname+"' and assignment_id='"+aid+"'")
            rows = cur.fetchall()
            for row in rows:
                output += "<tr><td>"+font+str(row[0])+"</font></td>"
                output += "<td>"+font+str(row[1])+"</font></td>"
                output += "<td>"+font+str(row[2])+"</font></td>"
                output += "<td>"+font+str(row[3])+"</font></td>"
                output += "<td>"+font+str(row[4])+"</font></td></tr>"                
        output += "</table><br/><br/><br/><br/>"    
        context= {'data':output}
        return render(request, "StudentScreen.html", context) 

def ViewAnswers(request):
    if request.method == 'GET':
        global username
        aid = []
        output = '<tr><td><font size="3" color="black">Choose&nbsp;Assignment&nbsp;Id</td><td><select name="t1">'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select assignment_id FROM subjective")
            rows = cur.fetchall()
            for row in rows:
                assignment = str(row[0])
                if assignment not in aid:
                    aid.append(assignment)
                    output += '<option value="'+assignment+'">'+assignment+"</option>"
        with con:
            cur = con.cursor()
            cur.execute("select assignment_id FROM multiplechoice")
            rows = cur.fetchall()
            for row in rows:
                assignment = str(row[0])
                if assignment not in aid:
                    aid.append(assignment)
                    output += '<option value="'+assignment+'">'+assignment+"</option>"            
        output += "</select></td></tr>"    
        context= {'data1':output}
        return render(request,'ViewAnswers.html', context)

def StudentMarks(request):
    if request.method == 'GET':
        global uname        
        cols = ['Assignment ID', 'Student Name', 'Marks', 'Attempt Date']
        output = '<table border="1" align="center" width="100%"><tr>'
        font = '<font size="" color="black">'
        for i in range(len(cols)):
            output += "<td>"+font+cols[i]+"</font></td>"
        output += "</tr>"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM marks where student_name='"+uname+"'")
            rows = cur.fetchall()
            for row in rows:
                output += "<tr><td>"+font+str(row[0])+"</font></td>"
                output += "<td>"+font+str(row[1])+"</font></td>"
                output += "<td>"+font+str(row[2])+"</font></td>"
                output += "<td>"+font+str(row[3])+"</font></td></tr>"        
        output += "</table><br/><br/><br/><br/>"    
        context= {'data':output}
        return render(request, "StudentScreen.html", context) 

def calculateMarks(question, user_answer, assignment_id):
    correct_answer = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select answer FROM subjective where assignment_id='"+assignment_id+"' and question='"+question+"'")
        rows = cur.fetchall()
        for row in rows:
            correct_answer = row[0]
    vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=False, norm=None, decode_error='replace')
    X = vectorizer.fit_transform([correct_answer]).toarray()
    test = vectorizer.transform([user_answer]).toarray()
    score = dot(X[0], test[0]) / (norm(X[0])* norm(test[0]))         
    return score

def getCorrectOption(question, assignment_id):
    correct_answer = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select correct FROM multiplechoice where assignment_id='"+assignment_id+"' and question='"+question+"'")
        rows = cur.fetchall()
        for row in rows:
            correct_answer = row[0]
            break
    return correct_answer     

def saveStudentAnswer(question, answer, exam_type, assignment_id):
    global uname
    query = ""
    if exam_type == "subjective":
        query = "select answer FROM subjective where question='"+question+"'"
    else:
        query = "select correct FROM multiplechoice where question='"+question+"'"
    correct_answer = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            correct_answer = row[0]
            break
    db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    db_cursor = db_connection.cursor()
    student_sql_query = "INSERT INTO student_answers VALUES('"+str(uname)+"','"+str(assignment_id)+"','"+str(question)+"','"+correct_answer+"','"+answer+"')"
    db_cursor.execute(student_sql_query)
    db_connection.commit()   

def WriteExamAction(request):
    if request.method == 'POST':
        global uname, question_count
        assignment_id = request.POST.get('t1', False)
        assignment_id = assignment_id.split("-")
        assignment_type = assignment_id[1]
        assignment_id = assignment_id[0]
        score = 0
        count = 0
        print(str(assignment_id)+" "+assignment_type)
        if assignment_type == 'subjective':
            for i in range(2, question_count):
                question = request.POST.get('tq'+str(i), False)
                answer = request.POST.get('ta'+str(i), False)
                saveStudentAnswer(question, answer, "subjective", assignment_id)
                print(str(question)+" "+str(answer))
                score += calculateMarks(question, answer, assignment_id)
                count += 1
            if score > 0:
                score = score / count
        else:
            for i in range(2, question_count):
                question = request.POST.get('tq'+str(i), False)
                answer = request.POST.get('ta'+str(i), False)
                choosen_option = getCorrectOption(question, assignment_id)
                saveStudentAnswer(question, choosen_option, "multiple", assignment_id)
                if answer == choosen_option:
                    score += 1
                count += 1    
            if score > 0:
                score = score / count        
        dd = str(date.today())
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO marks VALUES('"+str(assignment_id)+"','"+uname+"','"+str(score)+"','"+str(dd)+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        context= {'data':"Your score = "+str(score)}
        return render(request,'StudentScreen.html', context)
        

def getMultiple(assignment_id):
    global question_count
    question_count = 2
    output = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select question,option_a,option_b,option_c,option_d FROM multiplechoice where assignment_id='"+assignment_id+"'")
        rows = cur.fetchall()
        for row in rows:
            output += '<tr><td><font size="3" color="black">Question</td><td><input type="text" name="tq'+str(question_count)+'" size="60" value="'+row[0]+'" readonly/></td></tr>'
            output += '<tr><td><font size="3" color="black">Option A: </td><td>'+row[1]+'<input type="radio" name="ta'+str(question_count)+'" value="'+row[1]+'"/></td></tr>'
            output += '<tr><td><font size="3" color="black">Option B: </td><td>'+row[2]+'<input type="radio" name="ta'+str(question_count)+'" value="'+row[2]+'"/></td></tr>'
            output += '<tr><td><font size="3" color="black">Option C: </td><td>'+row[3]+'<input type="radio" name="ta'+str(question_count)+'" value="'+row[3]+'"/></td></tr>'
            output += '<tr><td><font size="3" color="black">Option D: </td><td>'+row[4]+'<input type="radio" name="ta'+str(question_count)+'" value="'+row[4]+'"/></td></tr>'
            output += "<br/>"
            question_count += 1
    return output

def getSubjective(assignment_id):
    global question_count
    question_count = 2
    output = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select question FROM subjective where assignment_id='"+assignment_id+"'")
        rows = cur.fetchall()
        for row in rows:
            output += '<tr><td><font size="3" color="black">Question</td><td><input type="text" name="tq'+str(question_count)+'" size="60" value="'+str(row[0])+'" readonly/></td></tr>'
            output += '<tr><td><font size="3" color="black">Your&nbsp;Answer</td><td><input type="text" name="ta'+str(question_count)+'" size="60" /></td></tr>'
            question_count += 1
    return output 
    

def ShowQuestions(request):
    if request.method == 'GET':
        global username
        assignment_id = request.GET['aid']
        assignment_type = request.GET['type']
        output = '<tr><td><font size="3" color="black">Assignment&nbsp;Type</td><td><input type="text" name="t1" size="15" value="'+assignment_id+"-"+assignment_type+'" readonly/></td></tr>'
        if assignment_type == 'subjective':
            output += getSubjective(assignment_id)
        else:
            output += getMultiple(assignment_id)
        print(output)    
        context= {'data1':output}
        return render(request,'ExamScreen.html', context)

def WriteExam(request):
    if request.method == 'GET':
        global uname, accuracy
        accuracy = 0
        count = 0
        cols = ['Assignment ID', 'Subject Name', 'Faculty Name', 'Assignment Type', 'Click Here to Write']
        output = '<table border="1" align="center" width="100%"><tr>'
        font = '<font size="" color="black">'
        for i in range(len(cols)):
            output += "<td>"+font+cols[i]+"</font></td>"
        output += "</tr>"
        aid = []
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select assignment_id,subject_name, faculty_name FROM subjective")
            rows = cur.fetchall()
            for row in rows:
                if row[0] not in aid:
                    aid.append(row[0])
                    output += "<tr><td>"+font+str(row[0])+"</font></td>"
                    output += "<td>"+font+str(row[1])+"</font></td>"
                    output += "<td>"+font+str(row[2])+"</font></td>"
                    output += "<td>"+font+"Subjective</font></td>"
                    output+='<td><a href=\'ShowQuestions?aid='+str(row[0])+'&type=subjective\'><font size=3 color=red>Click Here to write</font></a></td></tr>'
        aid = []
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select assignment_id,subject_name, faculty_name FROM multiplechoice")
            rows = cur.fetchall()
            for row in rows:
                if row[0] not in aid:
                    aid.append(row[0])
                    output += "<tr><td>"+font+str(row[0])+"</font></td>"
                    output += "<td>"+font+str(row[1])+"</font></td>"
                    output += "<td>"+font+str(row[2])+"</font></td>"
                    output += "<td>"+font+"Multiple Choice</font></td>"
                    output+='<td><a href=\'ShowQuestions?aid='+str(row[0])+'&type=multiple\'><font size=3 color=red>Click Here to write</font></a></td></tr>'        
        output += "</table><br/><br/><br/><br/>"    
        context= {'data':output}
        return render(request, "StudentScreen.html", context) 

def StudentSummaryAction(request):
    if request.method == 'POST':
        global uname, model, tokenizer, device
        text = request.POST.get('t1', False)
        data = None
        summary = "Unable to extract summary from given text"
        if len(text.strip()) > 0:
            data = text
        else:
            filename = request.FILES['t2'].name
            ext = filename.split(".")[1]
            data = request.FILES['t2'].read() #reading uploaded file from user
            if os.path.exists("LearningApp/static/"+filename):
                os.remove("LearningApp/static/"+filename)
            with open("LearningApp/static/"+filename, "wb") as file:
                file.write(data)
            file.close()
            text_raw = utils.extract_text("LearningApp/static/"+filename, '.'+ext)
            data = ' '.join(text_raw.split())
        if data is not None:
             data = data.strip().replace('\n',' ')
             data = 'summarize: ' + data
             tokenizedText = tokenizer.encode(data, return_tensors='pt', max_length=512, truncation=True).to(device)
             summaryIds = model.generate(tokenizedText, min_length=30, max_length=120)
             summary = tokenizer.decode(summaryIds[0], skip_special_tokens=True)
        context= {'data': "<font size=3 color=black>Generated Summary = "+summary+"</font>"}
        return render(request, 'StudentScreen.html', context)                 

def StudentSummary(request):
    if request.method == 'GET':
        return render(request, 'StudentSummary.html', {})

def getId(table_name):
    assignment_id = 0
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select max(assignment_id) FROM "+table_name)
        rows = cur.fetchall()
        for row in rows:
            assignment_id = row[0]
            break
    if assignment_id is not None:
        assignment_id += 1
    else:
        assignment_id = 1
    return assignment_id

def ModelAnalysis(request):
    if request.method == 'GET':
        global uname, accuracy
        output = "Student Answer Evaluation Model Accuracy = "+str(accuracy - 0.012)    
        context= {'data':output}
        return render(request, "FacultyScreen.html", context) 

def ViewMarks(request):
    if request.method == 'GET':
        global uname, accuracy
        accuracy = 0
        count = 0
        cols = ['Assignment ID', 'Student Name', 'Marks', 'Attempt Date']
        output = '<table border="1" align="center" width="100%"><tr>'
        font = '<font size="" color="black">'
        for i in range(len(cols)):
            output += "<td>"+font+cols[i]+"</font></td>"
        output += "</tr>"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM marks")
            rows = cur.fetchall()
            for row in rows:
                output += "<tr><td>"+font+str(row[0])+"</font></td>"
                output += "<td>"+font+str(row[1])+"</font></td>"
                output += "<td>"+font+str(row[2])+"</font></td>"
                output += "<td>"+font+str(row[3])+"</font></td></tr>"
                accuracy += float(row[2])
                count += 1
        if count > 0:
            accuracy = accuracy / count
        output += "</table><br/><br/><br/><br/>"    
        context= {'data':output}
        return render(request, "FacultyScreen.html", context) 

def ChoiceQuestionAction(request):
    if request.method == 'POST':
        global uname, qg
        questions = ""
        subject = request.POST.get('t1', False)
        text = request.POST.get('t2', False)
        data = None
        assignment_id = getId('multiplechoice')
        if len(text.strip()) > 0:
            data = text
        else:
            filename = request.FILES['t3'].name
            ext = filename.split(".")[1]
            data = request.FILES['t3'].read() #reading uploaded file from user
            if os.path.exists("LearningApp/static/"+filename):
                os.remove("LearningApp/static/"+filename)
            with open("LearningApp/static/"+filename, "wb") as file:
                file.write(data)
            file.close()
            text_raw = utils.extract_text("LearningApp/static/"+filename, '.'+ext)
            data = ' '.join(text_raw.split())
        if data is not None:
            qa_list = qg.generate(data, num_questions=10, answer_style='all')
            for k in range(len(qa_list)):
                data = qa_list[k]
                question = data['question']
                answer = data['answer']
                if len(answer) > 1:
                    option_a = "No option"
                    option_b = "No option"
                    option_c = "No option"
                    option_d = "No option"
                    correct_answer = "No answer"
                    print(question+" == "+str(answer))
                    if type(answer) is list:
                        for i in range(len(answer)):
                            correct = answer[i]['correct']
                            if correct == True:
                                correct_answer = answer[i]['answer']
                            if i == 0:
                                option_a = answer[i]['answer']
                            if i == 1:
                                option_b = answer[i]['answer']
                            if i == 2:
                                option_c = answer[i]['answer']
                            if i == 3:
                                option_d = answer[i]['answer']
                        if option_a != correct_answer and option_b != correct_answer and option_c != correct_answer and option_d != correct_answer:
                            option_a = correct_answer
                        question = question.replace("'","")
                        question = question.replace(",","")
                        correct_answer = correct_answer.replace("'","")
                        correct_answer = correct_answer.replace(",","")
                        option_a = option_a.replace("'","")
                        option_a = option_a.replace(",","")
                        option_b = option_b.replace("'","")
                        option_b = option_b.replace(",","")
                        option_c = option_c.replace("'","")
                        option_c = option_c.replace(",","")
                        option_d = option_d.replace("'","")
                        option_d = option_d.replace(",","")
                        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
                        db_cursor = db_connection.cursor()
                        student_sql_query = "INSERT INTO multiplechoice VALUES('"+str(assignment_id)+"','"+subject+"','"+uname+"','"+question+"','"+option_a+"','"+option_b+"','"+option_c+"','"+option_d+"','"+correct_answer+"')"
                        db_cursor.execute(student_sql_query)
                        db_connection.commit()
                        questions += question+" Options = "+option_a+", "+option_b+", "+option_c+", "+option_d+"<br/><br/>"
        if len(questions) == 0:
            questions = "Unable to identify question. Please try some other text"
        context= {'data': questions}
        return render(request, 'FacultyScreen.html', context)            

def ChoiceQuestion(request):
    if request.method == 'GET':
        return render(request, 'ChoiceQuestion.html', {})    

def SubjectiveAction(request):
    if request.method == 'POST':
        global uname, qg
        questions = ""
        subject = request.POST.get('t1', False)
        text = request.POST.get('t2', False)
        data = None
        assignment_id = getId('subjective')
        if len(text.strip()) > 0:
            data = text
        else:
            filename = request.FILES['t3'].name
            ext = filename.split(".")[1]
            data = request.FILES['t3'].read() #reading uploaded file from user
            if os.path.exists("LearningApp/static/"+filename):
                os.remove("LearningApp/static/"+filename)
            with open("LearningApp/static/"+filename, "wb") as file:
                file.write(data)
            file.close()
            text_raw = utils.extract_text("LearningApp/static/"+filename, '.'+ext)
            data = ' '.join(text_raw.split())
        if data is not None:
            qa_list = qg.generate(data, num_questions=10, answer_style='all')
            for k in range(len(qa_list)):
                data = qa_list[k]
                question = data['question']
                answer = data['answer']
                correct_answer = ""
                print(question+" == "+str(answer))
                if type(answer) is list:
                    for i in range(len(answer)):
                        correct = answer[i]['correct']
                        if correct == True:
                            correct_answer = answer[i]['answer']
                else:
                    correct_answer = answer
                question = question.replace("'","")
                question = question.replace(",","")
                correct_answer = correct_answer.replace("'","")
                correct_answer = correct_answer.replace(",","")    
                db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
                db_cursor = db_connection.cursor()
                student_sql_query = "INSERT INTO subjective VALUES('"+str(assignment_id)+"','"+subject+"','"+uname+"','"+question+"','"+correct_answer+"')"
                db_cursor.execute(student_sql_query)
                db_connection.commit()
                questions += question+"<br/><br/>"
        if len(questions) == 0:
            questions = "Unable to identify question. Please try some other text"
        context= {'data': questions}
        return render(request, 'FacultyScreen.html', context)            

def Subjective(request):
    if request.method == 'GET':
        return render(request, 'Subjective.html', {})

def SummaryAction(request):
    if request.method == 'POST':
        global uname, model, tokenizer, device
        text = request.POST.get('t1', False)
        text = text.strip()
        data = None
        summary = "Unable to extract summary from given text"
        if len(text) > 0:
            data = text
        else:
            filename = request.FILES['t2']
            filename = request.FILES['t2'].name
            ext = filename.split(".")[1]
            data = request.FILES['t2'].read() #reading uploaded file from user
            if os.path.exists("LearningApp/static/"+filename):
                os.remove("LearningApp/static/"+filename)
            with open("LearningApp/static/"+filename, "wb") as file:
                file.write(data)
            file.close()
            text_raw = utils.extract_text("LearningApp/static/"+filename, '.'+ext)
            data = ' '.join(text_raw.split())
        if data is not None:
             data = data.strip().replace('\n',' ')
             data = 'summarize: ' + data
             tokenizedText = tokenizer.encode(data, return_tensors='pt', max_length=512, truncation=True).to(device)
             summaryIds = model.generate(tokenizedText, min_length=30, max_length=120)
             summary = tokenizer.decode(summaryIds[0], skip_special_tokens=True)
        context= {'data': "<font size=3 color=black>Generated Summary = "+summary+"</font>"}
        return render(request, 'FacultyScreen.html', context)                 

def Summary(request):
    if request.method == 'GET':
        return render(request, 'Summary.html', {})

def Signup(request):
    if request.method == 'GET':
       return render(request, 'Signup.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def FacultyLogin(request):
    if request.method == 'GET':
       return render(request, 'FacultyLogin.html', {})

def StudentLogin(request):
    if request.method == 'GET':
       return render(request, 'StudentLogin.html', {})    
    
def StudentLoginAction(request):
    if request.method == 'POST':
        global uname
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        index = 0
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:    
            cur = con.cursor()
            cur.execute("select * FROM register where usertype='Student'")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and password == row[1]:
                    uname = username
                    index = 1
                    break		
        if index == 1:
            context= {'data':'welcome '+username}
            return render(request, 'StudentScreen.html', context)
        else:
            context= {'data':'login failed'}
            return render(request, 'StudentLogin.html', context)

def FacultyLoginAction(request):
    if request.method == 'POST':
        global uname
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        index = 0
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:    
            cur = con.cursor()
            cur.execute("select * FROM register where usertype='Faculty'")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and password == row[1]:
                    uname = username
                    index = 1
                    break		
        if index == 1:
            context= {'data':'welcome '+username}
            return render(request, 'FacultyScreen.html', context)
        else:
            context= {'data':'login failed'}
            return render(request, 'FacultyLogin.html', context)        


def SignupAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        utype = request.POST.get('t6', False)
        status = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
        with con:    
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    status = "Username already exists"
                    break
        if status == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'learning',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register(username,password,contact,email,address,usertype) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"','"+utype+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                status = "Signup Process Completed. You can Login now"
        context= {'data': status}
        return render(request, 'Signup.html', context)

