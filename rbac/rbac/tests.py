# from django.test import TestCase

# Create your tests here.
import qrcode


# def getQRcode(date, fileName):
def getQRcode(url, fileName):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img.save(fileName)


if __name__ == '__main__':
    # wz = 'http://'
    # for i in range(1000):
    #     url = wz + str(i).zfill(6)
    #     getQRcode(url, str(i).zfill(6) + '.png')
    file_name = 'baidu.png'
    getQRcode('https://blog.csdn.net/weixin_30291791/article/details/98918713', 'mz.png')
