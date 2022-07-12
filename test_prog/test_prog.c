#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>


int main() {
    printf("HELLO\n");
    int fd1, fd2, fd3, fd4;
    FILE *fptr1, *fptr2, *fptr3, *fptr4, *fptr5, *fptr6;
    char buf[32000] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;
    char *fn1 = "./tmp1.txt";
    char *fn2 = "./tmp2.txt";
    char *fn3 = "./tmp3.txt";
    char *fn4 = "./tmp4.txt";

    fd1 = open(fn1, O_WRONLY);
    fd2 = open(fn2, O_RDONLY);
    fd3 = open(fn3, O_RDWR);
    fd4 = open(fn4, O_WRONLY | O_APPEND | O_CREAT | O_TRUNC);

    fptr1 = fopen("./tmp1_isoc.txt", "w");
    fptr2 = fopen("./tmp2_isoc.txt", "r");
    fptr3 = fopen("./tmp3_isoc.txt", "r+");
    fptr4 = fopen("./tmp4_isoc.txt", "w+");
    fptr5 = fopen("./tmp5_isoc.txt", "a");
    fptr6 = fopen("./tmp6_isoc.txt", "a+");


    write(fd1, buf, sizeof(buf));
    write(fd4, buf, sizeof(buf));

    close(fd1);
    close(fd2);
    close(fd3);
    close(fd4);

    fclose(fptr1);
//    fclose(fptr2);
//    fclose(fptr3);
    fclose(fptr4);
    fclose(fptr5);
    fclose(fptr6);



    return 0;
}