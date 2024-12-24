let isLoggedIn = false;

let currentUserId = null;

let allowPageClose = false; // 标志变量，控制页面是否允许关闭

// 显示确认模态窗
function showConfirmationModal(message, action) {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('confirmation-modal');
  const modalMessage = document.getElementById('modal-message');

  modalMessage.textContent = message;
  overlay.classList.remove('hidden');
  modal.classList.remove('hidden');
  currentAction = action;
}

// 隐藏确认模态窗
function hideConfirmationModal() {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('confirmation-modal');

  overlay.classList.add('hidden');
  modal.classList.add('hidden');
  currentAction = null;
}

// 绑定模态窗按钮
document.getElementById('confirm-action').onclick = () => {
  if (currentAction) currentAction(); // 执行当前操作
  hideConfirmationModal();
};

// 显示模态窗
function showModal(title, message, action = null) {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('confirmation-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalMessage = document.getElementById('modal-message');

  modalTitle.textContent = title;
  modalMessage.textContent = message;

  overlay.classList.remove('hidden');
  modal.classList.remove('hidden');
  currentAction = action;
}

// 隐藏模态窗
function hideModal() {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('confirmation-modal');

  overlay.classList.add('hidden');
  modal.classList.add('hidden');
}

// 绑定模态窗按钮
document.getElementById('confirm-action').onclick = () => {
  if (currentAction) currentAction(); // 执行当前操作
  hideModal();
};

document.getElementById('cancel-action').onclick = hideModal;

// 显示通知条
function showNotification(title, content) {
  const container = document.getElementById('notification-container');
  const notification = document.createElement('div');

  notification.className = 'notification';
  notification.innerHTML = `
<div class="notification-title">${title}</div>
<div class="notification-content">${content}</div>
`;

  container.appendChild(notification);

  // 自动移除通知条
  setTimeout(() => {
    notification.remove();
  }, 1700); // 动画结束后删除
}

document.getElementById('cancel-action').onclick = hideConfirmationModal;

function showLogin() {
  document.getElementById('login-section').classList.remove('hidden');
  document.getElementById('register-section').classList.add('hidden');
}

function showRegister() {
  document.getElementById('login-section').classList.add('hidden');
  document.getElementById('register-section').classList.remove('hidden');
}

function login() {
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  fetch('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username,
        password
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        currentUserId = data.user_id;
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('main-section').classList.remove('hidden');
        fetchFiles();
        isLoggedIn = true; // 用户已登录
        updateTopBar(username);
        showNotification(username + ' 登录成功', '欢迎回来！');

      } else {
        isLoggedIn = false;
        showNotification('登录失败', data.message);

      }
    });
}

function register() {
  const username = document.getElementById('register-username').value;
  const password = document.getElementById('register-password').value;

  fetch('/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username,
        password
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showNotification('注册成功', '请登录以开始使用！');
        showLogin();
      } else {
        alert(data.message);
      }
    });
}

function logout() {
  showConfirmationModal('您确定要退出登录吗？', () => {
    fetch('/logout', {
        method: 'POST'
      })
      .then(() => {
        document.getElementById('main-section').classList.add('hidden');
        showLogin();
        updateTopBar("未登录");
        showNotification('成功', '您已成功退出登录。');
        isLoggedIn = false;
      });
  });
}

function fetchFiles() {
  fetch('/files')
    .then(res => res.json())
    .then(data => {
      const tableBody = document.getElementById('file-table-body');
      tableBody.innerHTML = '';
      data.forEach(file => {
        const row = `<tr>
          <td>${file.file_name}</td>
          <td>${file.uploaded_at}</td>
          <td class="button-group">
            <button class="action-button download" onclick="downloadFile('${file.file_uuid}', '${file.file_name}')">下载</button>
            <button class="action-button delete" onclick="deleteFile('${file.file_uuid}')">删除</button>
            ${file.is_shared 
              ? `<button class="action-button share" onclick="showShareInfo('${file.file_uuid}')">查看分享</button>`
              : `<button class="action-button share" onclick="shareFile('${file.file_uuid}')">分享</button>`
            }
          </td>
        </tr>`;
        tableBody.innerHTML += row;
      });
    });
}

function uploadFile() {
  const fileInput = document.getElementById('file-upload');
  if (fileInput.files.length === 0) {
    showModal('提示', '请选择一个文件后再上传！');
    return;
  }
  showConfirmationModal('您确定要上传该文件吗？', () => {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const file = fileInput.files[0];
    const fileName = file.name; // 获取文件名
    showNotification('上传开始', `正在上传文件：${fileName}`);
    fetch('/upload', {
        method: 'POST',
        body: formData
      })
      .then(() => {
        showNotification('上传成功', '文件上传已开始。');
        fetchFiles();
      });
  });
}

function downloadFile(fileUuid, fileName) {
  const link = document.createElement('a');
  link.href = `/download/${fileUuid}`;
  link.download = fileName; // 设置下载的文件名
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


function deleteFile(fileUuid) {
  showConfirmationModal('您确定要删除该文件吗？', () => {
    fetch(`/delete/${fileUuid}`, {
        method: 'DELETE'
      })
      .then(() => {
        showNotification('删除成功', '文件已成功删除。');
        fetchFiles();
      });
  });
}

function showShareInfo(fileUuid) {
  fetch(`/api/share/${fileUuid}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    showShareModal(data.share_url, data.share_code, fileUuid);
  })
  .catch(error => {
    showNotification('错误', '获取分享信息失败');
  });
}

function showShareModal(shareUrl, shareCode, fileUuid) {
  const shareModal = document.getElementById('share-modal');
  const shareContent = document.getElementById('share-content');
  const fullShareUrl = window.location.origin + shareUrl;
  
  shareContent.innerHTML = `
    <div style="margin-bottom: 20px;">
      <p style="margin-bottom: 10px;"><strong>分享链接：</strong></p>
      <div style="background: #f5f5f5; padding: 10px; border-radius: 4px; word-break: break-all;">
        ${fullShareUrl}
      </div>
    </div>
    <div style="margin-bottom: 20px;">
      <p style="margin-bottom: 10px;"><strong>分享密码：</strong></p>
      <div style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 1.2em;">
        ${shareCode}
      </div>
    </div>
    <div style="display: flex; gap: 10px; justify-content: center;">
      <button onclick="copyShareInfo('${fullShareUrl}', '${shareCode}')" 
              style="background: #4CAF50;">复制分享信息</button>
      <button onclick="unshareFile('${fileUuid}')" 
              style="background: #f44336;">取消分享</button>
    </div>
  `;
  
  shareModal.classList.remove('hidden');
  document.getElementById('modal-overlay').classList.remove('hidden');
}

function copyShareInfo(url, code) {
  const text = `链接：${url}\n密码：${code}`;
  navigator.clipboard.writeText(text)
    .then(() => {
      showNotification('成功', '分享信息已复制到剪贴板');
    })
    .catch(() => {
      showNotification('错误', '复制失败');
    });
}

function shareFile(fileUuid) {
  fetch(`/api/share/${fileUuid}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  })
  .then(res => {
    if (!res.ok) throw new Error('分享失败');
    return res.json();
  })
  .then(data => {
    showShareModal(data.share_url, data.share_code, fileUuid);
    fetchFiles(); // 刷新文件列表以更新按钮状态
  })
  .catch(error => {
    showNotification('错误', error.message || '分享文件时发生错误');
  });
}

function unshareFile(fileUuid) {
  fetch(`/share/${fileUuid}`, {
    method: 'DELETE'
  })
  .then(res => {
    if (!res.ok) throw new Error('取消分享失败');
    document.getElementById('share-modal').classList.add('hidden');
    document.getElementById('modal-overlay').classList.add('hidden');
    showNotification('成功', '已取消分享');
    fetchFiles(); // 刷新文件列表以更新按钮状态
  })
  .catch(error => {
    showNotification('错误', error.message || '取消分享失败');
  });
}

// 控制顶部栏和显示用户名
function updateTopBar(username) {
  const topBarTitle = document.getElementById('top-bar-title');
  const logoutBtn = document.getElementById('logout-button');
  const destroyBtn = document.getElementById('destroy-account-button');
  if (username) {
    topBarTitle.textContent = `328 文件云盘 | 欢迎, ${username}`;
    logoutBtn.classList.remove('hidden');
    destroyBtn.classList.remove('hidden');
  } else {
    topBarTitle.textContent = '328 文件云盘';
    logoutBtn.classList.add('hidden');
    destroyBtn.classList.add('hidden');
  }
}

// 添加销毁账户相关函数
let confirmationCount = 0;
const requiredConfirmations = 3;

document.getElementById('destroy-account-button').addEventListener('click', initiateAccountDestruction);

function initiateAccountDestruction() {
  let currentStep = 1;
  showNextConfirmation();

  function showNextConfirmation() {
    if (currentStep <= 3) {
      const overlay = document.getElementById('modal-overlay');
      const modal = document.getElementById('confirmation-modal');
      const modalTitle = document.getElementById('modal-title');
      const modalMessage = document.getElementById('modal-message');

      modalTitle.textContent = '警告';
      modalMessage.textContent = `确定要删除账户吗？这是第 ${currentStep} 次确认，共需确认 3 次。此操作将永久删除您的所有数据！`;

      overlay.classList.remove('hidden');
      modal.classList.remove('hidden');

      // 重新绑定确认按钮事件
      document.getElementById('confirm-action').onclick = () => {
        currentStep++;
        overlay.classList.add('hidden');
        modal.classList.add('hidden');
        showNextConfirmation();
      };

      // 重新绑定取消按钮事件
      document.getElementById('cancel-action').onclick = () => {
        overlay.classList.add('hidden');
        modal.classList.add('hidden');
        currentStep = 1; // 重置步骤
      };
    } else {
      showFinalConfirmation();
    }
  }
}

function showFinalConfirmation() {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('delete-account-modal');
  
  overlay.classList.remove('hidden');
  modal.classList.remove('hidden');

  // 绑定新的确认和取消按钮事件
  document.getElementById('confirm-delete').onclick = executeAccountDestruction;
  document.getElementById('cancel-delete').onclick = () => {
    overlay.classList.add('hidden');
    modal.classList.add('hidden');
  };
}

function executeAccountDestruction() {
  const password = document.getElementById('confirm-password').value;
  const confirmText = document.getElementById('confirm-text').value;
  
  if (confirmText !== '我真的要删除这个账户') {
    showNotification('错误', '确认文字输入不正确');
    return;
  }
  
  fetch('/api/destroy-account', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ password })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      // 关闭删除账户的模态窗
      document.getElementById('delete-account-modal').classList.add('hidden');
      
      // 创建新的模态窗内容
      const modalContent = `
        <div class="modal-content">
          <h2 style="text-align: center;">您的冒险暂时告一段落，但大门永远为您敞开。<br>账户已成功注销，期待您的下一次归来！<br>再会了，朋友！</h2>
          <div class="modal-footer">
            <button style="text-align: center;" onclick="window.location.reload()">刷新页面</button>
          </div>
        </div>
      `;
      
      // 显示新的模态窗
      const modal = document.getElementById('confirmation-modal');
      modal.innerHTML = modalContent;
      modal.classList.remove('hidden');
      document.getElementById('modal-overlay').classList.remove('hidden');
    } else {
      showNotification('错误', data.message || '删除失败');
    }
  })
  .catch(error => {
    showNotification('错误', '操作失败');
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('file-upload');
  const clearButton = document.getElementById('clear-button');
  const fileNameSpan = document.getElementById('file-name');

  // 当文件被选择时更新文件名显示
  fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
      fileNameSpan.textContent = fileInput.files[0].name;
    } else {
      fileNameSpan.textContent = '';
    }
  });

  // 清空文件选择
  clearButton.addEventListener('click', function() {
    fileInput.value = ''; // 清空文件输入框的值
    fileNameSpan.textContent = ''; // 清空文件名显示
    showNotification('已清空', "当前文件选择已清空");
  });

  const fileUploadLabel = document.querySelector('.custom-file-upload');
  fileUploadLabel.addEventListener('click', function(event) {
    event.preventDefault(); // 阻止默认点击行为，防止重复弹窗
    document.getElementById('file-upload').click();
  });

  // 监听页面关闭事件
  window.addEventListener('beforeunload', (event) => {
    if (isLoggedIn && !allowPageClose) {
      // 显示自定义模态窗，阻止页面直接关闭
      event.preventDefault(); // 仅阻止默认行为，但不触发系统提示
      showConfirmCloseModal();
    }
  });

  // 显示自定义模态窗
  function showConfirmCloseModal() {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('confirm-close-modal');

    overlay.classList.remove('hidden');
    modal.classList.remove('hidden');

    document.getElementById('confirm-close').onclick = () => {
      allowPageClose = true; // 标记允许关闭页面
      overlay.classList.add('hidden');
      modal.classList.add('hidden');
      window.close(); // 控制关闭页面
    };

    document.getElementById('cancel-close').onclick = () => {
      overlay.classList.add('hidden');
      modal.classList.add('hidden');
    };
  }


  // 显示模态窗
  function showModal(title, message, action = null) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('confirmation-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');

    modalTitle.textContent = title;
    modalMessage.textContent = message;

    overlay.classList.remove('hidden');
    modal.classList.remove('hidden');
    currentAction = action;
  }

  // 隐藏模态窗
  function hideModal() {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('confirmation-modal');

    overlay.classList.add('hidden');
    modal.classList.add('hidden');
    currentAction = null;
  }

  // 绑定模态窗按钮
  document.getElementById('confirm-action').onclick = () => {
    if (currentAction) currentAction(); // 执行当前操作
    hideModal();
  };

  document.getElementById('cancel-action').onclick = hideModal;


});
