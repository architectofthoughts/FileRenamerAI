import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from anthropic import Anthropic
import sys
import traceback
from datetime import datetime

def show_error_and_exit(error_msg):
    """오류 메시지를 보여주고 사용자 입력을 기다립니다."""
    print(f"오류가 발생했습니다: {error_msg}")
    print("\n전체 오류 내용:")
    traceback.print_exc()
    input("\n아무 키나 누르면 프로그램이 종료됩니다...")
    sys.exit(1)

class FileRenamerGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("파일 이름 변경 도우미")
            self.root.geometry("600x400")
            
            # 스타일 설정
            style = ttk.Style()
            style.configure('TButton', padding=5)
            style.configure('TLabel', padding=5)
            
            # 메인 프레임
            main_frame = ttk.Frame(root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # API 키 저장 변수 추가
            self._default_api_key = None  # 실제 API 키를 저장할 private 변수
            
            # API 키 입력 프레임
            api_frame = ttk.Frame(main_frame)
            api_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
            
            # API 키 입력
            ttk.Label(api_frame, text="Anthropic API 키:").grid(row=0, column=0, sticky=tk.W)
            self.api_key = ttk.Entry(api_frame, width=50)
            self.api_key.grid(row=0, column=1, sticky=(tk.W, tk.E))
            
            # API 키 없음 버튼
            ttk.Button(api_frame, text="API 키가 없습니다", 
                      command=self.use_default_api_key).grid(row=0, column=2, padx=5)
            
            # 폴더 선택 프레임 (row 1)
            folder_frame = ttk.Frame(main_frame)
            folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
            
            ttk.Label(folder_frame, text="대상 폴더:").grid(row=0, column=0, sticky=tk.W)
            self.folder_path = ttk.Entry(folder_frame, width=50)
            self.folder_path.grid(row=0, column=1, sticky=(tk.W, tk.E))
            ttk.Button(folder_frame, text="찾아보기", 
                       command=self.browse_folder).grid(row=0, column=2, padx=5)
            
            # 추가 요청사항 입력 프레임 (row 2)
            request_frame = ttk.Frame(main_frame)
            request_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(request_frame, text="추가 요청사항").grid(row=0, column=0, sticky=tk.W)
            self.additional_request = tk.Text(request_frame, height=3, width=50)
            self.additional_request.grid(row=0, column=1, sticky=(tk.W, tk.E))
            
            # 진행 상황 표시 (row 3)
            self.progress_var = tk.StringVar(value="준비됨")
            ttk.Label(main_frame, textvariable=self.progress_var).grid(row=3, column=0, columnspan=3)
            
            # 파일 목록 표시 (row 4)
            self.file_list = tk.Text(main_frame, height=15, width=70)
            self.file_list.grid(row=4, column=0, columnspan=3, pady=10)
            
            # 파일 이름 변경 기록 저장용 딕셔너리 추가
            self.rename_history = {}
            
            # 버튼 프레임 추가
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=5, column=0, columnspan=3, pady=10)
            
            # 버튼 배치 수정
            ttk.Button(button_frame, text="파일 이름 변경 시작", 
                      command=self.process_files).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="원래 이름으로 복구", 
                      command=self.restore_original_names).grid(row=0, column=1, padx=5)

        except Exception as e:
            show_error_and_exit(str(e))

    def use_default_api_key(self):
        """기본 API 키를 설정하고 마스킹된 값을 표시합니다."""
        self._default_api_key = "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"
        
        # 입력창에는 마스킹된 값만 표시
        self.api_key.delete(0, tk.END)
        self.api_key.insert(0, "*" * 30 + " (기본 API 키 사용 중)")
        self.api_key.config(state='readonly')  # 편집 불가능하게 설정
        
        warning_message = """주의: 이 API 키를 사용하면 키 소유자(바로 저임;;)의 비용이 발생합니다.
        
가능하다면 본인의 API 키를 발급받아 사용해주세요.
자세한 내용은 https://console.anthropic.com/ 를 참고하세요."""
        
        messagebox.showwarning("API 키 사용 주의", warning_message)

    def get_current_api_key(self):
        """현재 사용할 API 키를 반환합니다."""
        if self._default_api_key:
            return self._default_api_key
        return self.api_key.get()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.delete(0, tk.END)
            self.folder_path.insert(0, folder)
            self.update_file_list()

    def update_file_list(self):
        self.file_list.delete(1.0, tk.END)
        folder = self.folder_path.get()
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            self.file_list.insert(tk.END, "현재 파일 목록:\n\n")
            for file in files:
                self.file_list.insert(tk.END, f"- {file}\n")

    def get_file_info(self, folder_path):
        file_info_list = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_info = {
                    'original_name': filename,
                    'size': file_stat.st_size,
                    'created_time': file_stat.st_ctime,
                    'modified_time': file_stat.st_mtime,
                    'extension': os.path.splitext(filename)[1],
                    'path': file_path
                }
                file_info_list.append(file_info)
        return file_info_list

    def get_file_type(self, extension):
        """파일 확장자를 기반으로 파일 종류를 반환합니다."""
        extension = extension.lower()
        file_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'document': ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.odt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
            'executable': ['.exe', '.msi', '.bat'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp']
        }
        
        for file_type, extensions in file_types.items():
            if extension in extensions:
                return file_type
        return 'other'

    def get_new_filenames_from_claude(self, file_info_list, api_key):
        try:
            client = Anthropic(api_key=api_key)
            
            # 추가 요청사항 가져오기
            additional_request = self.additional_request.get("1.0", tk.END).strip()
            
            prompt = """다음 파일들의 메타데이터를 분석하여 각 파일의 내용을 더 잘 설명할 수 있는 새로운 파일 이름을 제안해주세요.
            
            규칙:
            1. 파일명 형식은 반드시 다음과 같아야 합니다: YYYYMMDD_파일종류_한글파일명
            2. 파일종류는 영어로 작성 (image, video, document 등)
            3. 파일명은 한글로 작성하되, 의미 단위로 언더바(_)를 사용하여 구분
            4. 날짜는 YYYYMMDD 형식으로 파일명 맨 앞에 위치
            5. 파일 확장자는 원본 유지
            
            예시:
            - 20240320_image_제주도_풍경_사진.jpg
            - 20240320_document_회사_보고서_초안.pdf
            - 20240320_video_가족_여행_영상.mp4
            """
            
            # 추가 요청사항이 있는 경우에만 포함
            if additional_request:
                prompt += f"\n추가 요청사항:\n{additional_request}\n"
            
            prompt += """
            파일명에서 단어 구분을 위해 반드시 언더바(_)를 사용하여 읽기 쉽게 만들어주세요.
            
            파일 메타데이터:"""
            prompt += json.dumps(file_info_list, ensure_ascii=False, indent=2)
            prompt += "\n\n새로운 파일 이름을 다음 JSON 형식으로 제안해주세요: {\"renamed_files\": [{\"original\": \"원본이름.확장자\", \"new\": \"새이름.확장자\"}]}"

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_content = response.content[0].text
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            json_str = response_content[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            messagebox.showerror("오류", f"Claude API 호출 중 오류 발생: {str(e)}")
            return None

    def process_files(self):
        if not self.get_current_api_key():
            messagebox.showerror("오류", "API 키를 입력해주세요.")
            return
            
        if not self.folder_path.get():
            messagebox.showerror("오류", "폴더를 선택해주세요.")
            return
            
        self.progress_var.set("파일 정보 수집 중...")
        self.root.update()
        
        file_info_list = self.get_file_info(self.folder_path.get())
        
        self.progress_var.set("Claude API 호출 중...")
        self.root.update()
        
        rename_data = self.get_new_filenames_from_claude(
            file_info_list, 
            self.get_current_api_key()  # api_key.get() 대신 이 메서드 사용
        )
        
        if rename_data:
            self.progress_var.set("파일 이름 변경 중...")
            self.root.update()
            
            # 변경 내역 저장
            self.rename_history.clear()
            
            for file_info in rename_data["renamed_files"]:
                old_path = os.path.join(self.folder_path.get(), file_info["original"])
                new_path = os.path.join(self.folder_path.get(), file_info["new"])
                try:
                    os.rename(old_path, new_path)
                    # 변경 내역 저장
                    self.rename_history[new_path] = old_path
                except Exception as e:
                    messagebox.showerror("오류", f"파일 이름 변경 중 오류 발생: {str(e)}")
                    return
            
            # 변경 내역을 JSON 파일로 저장
            self.save_rename_history_to_json(rename_data)
            
            self.progress_var.set("완료됨")
            self.update_file_list()
            messagebox.showinfo("완료", "파일 이름 변경이 완료되었습니다.")
        else:
            self.progress_var.set("오류 발생")

    def restore_original_names(self):
        """변경된 파일 이름을 원래 이름으로 복구합니다."""
        if not self.rename_history:
            messagebox.showinfo("알림", "복구할 파일 변경 내역이 없습니다.")
            return
            
        self.progress_var.set("파일 이름 복구 중...")
        self.root.update()
        
        for new_path, old_path in self.rename_history.items():
            try:
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
            except Exception as e:
                messagebox.showerror("오류", f"파일 이름 복구 중 오류 발생: {str(e)}")
                return
        
        self.rename_history.clear()
        self.progress_var.set("복구 완료")
        self.update_file_list()
        messagebox.showinfo("완료", "파일 이름이 원래대로 복구되었습니다.")

    def save_rename_history_to_json(self, rename_data):
        """파일 이름 변경 내역을 JSON 파일로 저장합니다."""
        try:
            # 현재 날짜와 시간으로 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_filename = f"rename_history_{timestamp}.json"
            
            # 애플리케이션 폴더에 history 폴더 생성
            history_folder = "rename_history"
            if not os.path.exists(history_folder):
                os.makedirs(history_folder)
            
            history_path = os.path.join(history_folder, history_filename)
            
            # 변경 내역을 저장할 데이터 구조
            history_data = {
                "rename_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_folder": self.folder_path.get(),
                "renamed_files": [
                    {
                        "original": file_info["original"],
                        "new": file_info["new"]
                    }
                    for file_info in rename_data["renamed_files"]
                ]
            }
            
            # JSON 파일로 저장
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
            self.file_list.insert(tk.END, f"\n변경 내역이 {history_filename}에 저장되었습니다.\n")
        except Exception as e:
            messagebox.showerror("오류", f"변경 내역 저장 중 오류 발생: {str(e)}")

def main():
    try:
        root = tk.Tk()
        app = FileRenamerGUI(root)
        root.mainloop()
    except Exception as e:
        show_error_and_exit(str(e))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        show_error_and_exit(str(e))
