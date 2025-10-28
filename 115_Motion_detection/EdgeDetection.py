import cv2


# Uri

# Загрузка изображения
image = cv2.imread('images/LikeCT_2.jpg')

# Преобразование изображения в оттенки серого
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Применение фильтра Canny для обнаружения границ
edges = cv2.Canny(gray, 500, 550)       # sample 1-4
#edges = cv2.Canny(gray, 80, 160)        # sample 5-6

# Нахождение контуров на обработанных границах
contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

# Рисование контуров на оригинальном изображении
cv2.drawContours(image, contours, -1, (0, 255, 0), 2)

# Отображение результата
cv2.namedWindow("Contours", cv2.WINDOW_NORMAL)
cv2.imshow('Contours', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
