from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
import traceback
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///internships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# メールサーバーの設定
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

db = SQLAlchemy(app)
mail = Mail(app)
scheduler = APScheduler()

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text)
    priority = db.Column(db.Integer, nullable=False, default=5)  # Added priority field

@app.route('/')
def home():
    return render_template('index.html', message='マイインターンシップアプリへようこそ！')

@app.route('/about')
def about():
    return render_template('index.html', message='これはインターンシップ申請を管理するアプリです。')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        try:
            new_internship = Internship(
                company=request.form['company'],
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d'),
                email=request.form['email'],
                content=request.form['content'],
                priority=int(request.form['priority'])  # Capture priority
            )
            db.session.add(new_internship)
            db.session.commit()

            if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                try:
                    send_confirmation_email(new_internship)
                    flash('申請が完了し、確認メールを送信しました。', 'success')
                except Exception as mail_error:
                    print(f"Failed to send email: {str(mail_error)}")
                    flash('申請は完了しましたが、確認メールの送信に失敗しました。', 'warning')
            else:
                flash('申請が完了しました。（メール設定がされていないため、確認メールは送信されません）', 'info')

            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error in apply route: {str(e)}")
            traceback.print_exc()
            db.session.rollback()
            flash(f"申請処理中にエラーが発生しました: {str(e)}", 'error')
            return redirect(url_for('apply'))
    return render_template('apply.html')

@app.route('/calendar')
def calendar():
    try:
        internships = Internship.query.order_by(Internship.priority).all()  # Sort by priority
        return render_template('calendar.html', internships=internships)
    except Exception as e:
        print(f"Error in calendar route: {str(e)}")
        traceback.print_exc()
        flash(f"カレンダーの表示中にエラーが発生しました: {str(e)}", 'error')
        return redirect(url_for('home'))

@app.route('/calendar/save')
def save_calendar():
    try:
        internships = Internship.query.order_by(Internship.priority).all()  # Sort by priority
        file_path = 'calendar.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            for internship in internships:
                f.write(f"会社名: {internship.company}\n")
                f.write(f"開始日: {internship.start_date.strftime('%Y-%m-%d')}\n")
                f.write(f"終了日: {internship.end_date.strftime('%Y-%m-%d')}\n")
                f.write(f"優先順位: {internship.priority}\n")
                f.write(f"内容: {internship.content}\n")
                f.write("\n")
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"Error in save_calendar route: {str(e)}")
        traceback.print_exc()
        flash(f"カレンダーの保存中にエラーが発生しました: {str(e)}", 'error')
        return redirect(url_for('calendar'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    internship = Internship.query.get_or_404(id)
    if request.method == 'POST':
        try:
            internship.company = request.form['company']
            internship.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            internship.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            internship.email = request.form['email']
            internship.content = request.form['content']
            internship.priority = int(request.form['priority'])  # Capture priority
            db.session.commit()

            if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                try:
                    send_update_email(internship)
                except Exception as mail_error:
                    print(f"Failed to send update notification email: {str(mail_error)}")

            flash('インターンシップ情報が更新され、通知メールが送信されました。', 'success')
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error in edit route: {str(e)}")
            traceback.print_exc()
            db.session.rollback()
            flash(f"編集処理中にエラーが発生しました: {str(e)}", 'error')
            return redirect(url_for('edit', id=id))
    return render_template('edit.html', internship=internship)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    internship = Internship.query.get_or_404(id)
    try:
        if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            try:
                send_deletion_email(internship)
            except Exception as mail_error:
                print(f"Failed to send deletion notification email: {str(mail_error)}")

        db.session.delete(internship)
        db.session.commit()
        flash('インターンシップ情報が削除され、通知メールが送信されました。', 'success')
        return redirect(url_for('calendar'))
    except Exception as e:
        print(f"Error in delete route: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        flash(f"削除処理中にエラーが発生しました: {str(e)}", 'error')
        return redirect(url_for('calendar'))

def send_confirmation_email(internship):
    msg = Message('インターンシップ申請完了', recipients=[internship.email])
    msg.body = f"""
    インターンシップ申請が完了しました。

    会社名: {internship.company}
    開始日: {internship.start_date.strftime('%Y-%m-%d')}
    終了日: {internship.end_date.strftime('%Y-%m-%d')}
    優先順位: {internship.priority}
    内容: {internship.content}
    """
    mail.send(msg)
    save_notification_to_file('confirmation', msg)

def send_update_email(internship):
    msg = Message('インターンシップ申請の更新通知', recipients=[internship.email])
    msg.body = f"""
    以下のインターンシップ申請が更新されました。

    会社名: {internship.company}
    開始日: {internship.start_date.strftime('%Y-%m-%d')}
    終了日: {internship.end_date.strftime('%Y-%m-%d')}
    優先順位: {internship.priority}
    内容: {internship.content}

    ご不明な点がございましたら、お問い合わせください。
    """
    mail.send(msg)
    save_notification_to_file('update', msg)

def send_deletion_email(internship):
    msg = Message('インターンシップ申請の削除通知', recipients=[internship.email])
    msg.body = f"""
    以下のインターンシップ申請が削除されました。

    会社名: {internship.company}
    開始日: {internship.start_date.strftime('%Y-%m-%d')}
    終了日: {internship.end_date.strftime('%Y-%m-%d')}
    優先順位: {internship.priority}
    内容: {internship.content}

    ご不明な点がございましたら、お問い合わせください。
    """
    mail.send(msg)
    save_notification_to_file('deletion', msg)

@scheduler.task('cron', id='send_reminders', hour=10, minute=0)
def send_reminders():
    with app.app_context():
        today = datetime.now().date()
        one_week_later = today + timedelta(days=7)
        upcoming_internships = Internship.query.filter(
            Internship.start_date == one_week_later
        ).all()

        for internship in upcoming_internships:
            try:
                send_reminder_email(internship)
                print(f"Reminder sent for internship: {internship.id}")
            except Exception as e:
                print(f"Failed to send reminder for internship {internship.id}: {str(e)}")

def send_reminder_email(internship):
    subject = f"リマインダー: {internship.company}でのインターンシップが1週間後に開始します"
    body = f"""
    {internship.email}様

    {internship.company}でのインターンシップが1週間後に開始されることをお知らせします。

    開始日: {internship.start_date.strftime('%Y年%m月%d日')}
    終了日: {internship.end_date.strftime('%Y年%m月%d日')}
    優先順位: {internship.priority}
    内容: {internship.content}

    準備は整っていますか？何か質問がありましたら、お気軽にお問い合わせください。

    頑張ってください！
    """
    msg = Message(subject, recipients=[internship.email], body=body)
    mail.send(msg)
    save_notification_to_file('reminder', msg)

def save_notification_to_file(notification_type, msg):
    file_path = f"{notification_type}_notifications.txt"
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"--- {notification_type.capitalize()} Notification ---\n")
        f.write(f"To: {msg.recipients[0]}\n")
        f.write(f"Subject: {msg.subject}\n")
        f.write(f"Body:\n{msg.body}\n")
        f.write("\n")

@app.route('/debug-reset')
def debug_reset():
    try:
        init_db()
        flash('データベースをリセットしました。', 'success')
    except Exception as e:
        flash(f"データベースのリセット中にエラーが発生しました: {str(e)}", 'error')
    return redirect(url_for('home'))

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables created successfully")

if __name__ == '__main__':
    init_db()  # Initialize the database
    if not scheduler.running:  # Scheduler is only initialized if not already running
        scheduler.init_app(app)
        scheduler.start()
    app.run(debug=True, use_reloader=False)
