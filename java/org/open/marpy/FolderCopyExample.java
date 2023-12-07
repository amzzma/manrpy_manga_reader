package org.open.marpy;

import android.util.Log;
import org.apache.commons.io.FileUtils;
import java.io.File;
import java.io.IOException;

public class FolderCopyExample {

    public static void copyFolder(File source, File target) {
        try {
            FileUtils.copyDirectory(source, target);
            Log.d("FolderCopyExample", "文件夹拷贝成功！");
        } catch (IOException e) {
            Log.e("FolderCopyExample", "文件夹拷贝失败：" + e.getMessage());
        }
    }
}

