import base64
import gensim.parsing.preprocessing as gsp
import pandas as pd
import streamlit as st
import textdistance as td
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Hopefully we won't need this much
NUM_ITER = 20

def build_gmail_service(creds):
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred when trying to build gmail service: {error}")


def fetch_message_thread_by_id(service, thread_id):
    thread_data = service.users().threads().get(userId="me", id=thread_id).execute()
    return thread_data


def clean_content(msg_content: str):
    filters = [
        gsp.strip_tags,
        gsp.strip_punctuation,
        gsp.strip_multiple_whitespaces,
        gsp.strip_numeric,
    ]
    msg_content = msg_content.lower()
    for f in filters:
        msg_content = f(msg_content)
    return msg_content


def build_similarity_matrix(judge_emails):
    similarity_matrix = [
        [0 for _ in range(len(judge_emails))] for _ in range(len(judge_emails))
    ]
    cleaned_msg = [
        clean_content(judge_emails[i][2]).split() for i in range(len(judge_emails))
    ]
    for i in range(len(judge_emails)):
        for j in range(i + 1, len(judge_emails)):
            similarity_matrix[i][j] = similarity_matrix[j][i] = td.sorensen_dice(
                cleaned_msg[i], cleaned_msg[j]
            )
    return similarity_matrix


def get_all_judge_emails(creds):
    service = build_gmail_service(creds)
    num_judge_email = 0
    threads_req = service.users().threads().list(userId="me")
    judge_emails = []
    d = {
        "sender": [],
        "subject": [],
        "content": [],
        "most_similar_to": [],
        "similarity_score": [],
    }
    found = False
    for _ in range(NUM_ITER):
        threads_res = threads_req.execute()
        threads = threads_res.get("threads", [])
        for thread in threads:
            thread_data = fetch_message_thread_by_id(service, thread["id"])
            msg = thread_data["messages"][0]["payload"]
            subject = ""
            sender = ""
            date = None
            for header in msg["headers"]:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "Date":
                    date = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]
            if "Document shared with you" in subject:
                continue
            if "Major League Hacking" in sender:
                continue
            if not msg.get("parts"):
                continue
            decoded_data = ""
            for i in range(len(msg.get("parts"))):
                if msg.get("parts")[i]["mimeType"] in ["text/html", "text/plain"]:
                    data = msg.get("parts")[i]["body"]["data"]
                    data = data.replace("-", "+").replace("_", "/")
                    decoded_data = base64.b64decode(data)
                    break
            try:
                soup = BeautifulSoup(decoded_data, "lxml")
                body = soup.find_all("body")
                msg_content = body[0].get_text()
                if (
                    "judge" in msg_content
                    or "judging" in msg_content
                    or "Judge" in msg_content
                    or "Judging" in msg_content
                ):
                    judge_emails.append((sender, subject, msg_content))
                    # print(
                    #     f"Found new judging email from {sender} ({subject}) -> id = {len(judge_emails)-1}"
                    # )
                    num_judge_email += 1
                # First ever judging email received has this subject
                if subject == "Judging Opportunity : Hackutd":
                    found = True
                    break
            except:
                pass
        if found:
            break
        threads_req = service.users().threads().list_next(threads_req, threads_res)
    for e in judge_emails:
        d["sender"].append(e[0])
        d["subject"].append(e[1])
        d["content"].append(e[2])

    cleaned_msg = [
        clean_content(judge_emails[i][2][:]).split() for i in range(len(judge_emails))
    ]
    for i in range(len(judge_emails)):
        similarity = []
        for j in range(i + 1, len(judge_emails)):
            if judge_emails[i][0] == judge_emails[j][0]:
                continue
            similarity.append((j, td.sorensen_dice(cleaned_msg[i], cleaned_msg[j])))
        similarity.sort(key=lambda x: x[1], reverse=True)
        if not len(similarity):
            d["most_similar_to"].append(-1)
            d["similarity_score"].append(0)
        else:
            d["most_similar_to"].append(similarity[0][0])
            d["similarity_score"].append(similarity[0][1])
    return pd.DataFrame(data=d)
